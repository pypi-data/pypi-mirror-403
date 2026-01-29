"""JSONL log file monitoring for Claude CLI.

This module monitors Claude's JSONL log file for messages and events.
"""

import json
import os
import re
import threading
import time
from pathlib import Path
from typing import Any, Callable, Dict, Optional, Set, TYPE_CHECKING

from ..config import CLAUDE_LOG_BASE
from ..format_utils import format_content_block

if TYPE_CHECKING:
    from ..session_reset_handler import SessionResetHandler
    from ..messaging.processor import MessageProcessor
    from ..messaging.queue_manager import MessageQueue


class JSONLMonitor:
    """Monitors Claude's JSONL log file.

    Responsibilities:
    - Finding and watching the JSONL log file
    - Processing log entries
    - Handling session resets
    - Detecting subtasks
    """

    def __init__(
        self,
        agent_instance_id: str,
        message_processor: "MessageProcessor",
        reset_handler: "SessionResetHandler",
        log_func: Callable[[str], None],
        skip_existing_entries: bool = False,
        message_queue: Optional["MessageQueue"] = None,
        send_message_lock: Optional[threading.Lock] = None,
        requested_input_messages: Optional[Set[str]] = None,
        pending_permission_options: Optional[Dict[str, str]] = None,
    ):
        """Initialize JSONL monitor.

        Args:
            agent_instance_id: Agent instance ID
            message_processor: Message processor instance
            reset_handler: Session reset handler
            log_func: Logging function
            skip_existing_entries: Whether to skip existing entries on start
            message_queue: Message queue for queuing web messages to CLI
            send_message_lock: Lock for thread-safe message sending
            requested_input_messages: Set of messages we've requested input for
            pending_permission_options: Dict of pending permission options
        """
        self.agent_instance_id = agent_instance_id
        self.message_processor = message_processor
        self.reset_handler = reset_handler
        self.log = log_func
        self.skip_existing_entries = skip_existing_entries

        # Dependencies for message processing
        self.message_queue = message_queue
        self.send_message_lock = send_message_lock or threading.Lock()
        self.requested_input_messages = requested_input_messages or set()
        self.pending_permission_options = pending_permission_options or {}

        self.claude_jsonl_path: Optional[Path] = None
        self.running = True
        self.thread: Optional[threading.Thread] = None

    def start(self) -> None:
        """Start monitoring the JSONL file in a background thread."""
        if self.thread is not None:
            self.log("[WARNING] JSONL monitor thread already running")
            return

        self.running = True
        self.thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.thread.start()
        self.log("[INFO] Started JSONL monitor thread")

    def stop(self) -> None:
        """Stop monitoring.

        Note: This is a daemon thread, so we just signal it to stop.
        The thread will exit on its own when the main process exits.
        """
        self.running = False
        self.log("[INFO] Signaled JSONL monitor thread to stop")

    def get_project_log_dir(self) -> Optional[Path]:
        """Get the Claude project log directory for current working directory."""
        cwd = os.getcwd()
        # Convert path to Claude's format
        project_name = re.sub(r"[^a-zA-Z0-9]", "-", cwd)
        project_dir = CLAUDE_LOG_BASE / project_name
        return project_dir if project_dir.exists() else None

    def _monitor_loop(self) -> None:
        """Main monitoring loop (runs in background thread)."""
        # Wait for log file to be created
        while self.running and not self.claude_jsonl_path:
            project_dir = self.get_project_log_dir()
            if project_dir:
                expected_filename = f"{self.agent_instance_id}.jsonl"
                expected_path = project_dir / expected_filename
                if expected_path.exists():
                    self.claude_jsonl_path = expected_path
                    self.log(f"[INFO] Found Claude JSONL log: {expected_path}")
                    break
            time.sleep(0.5)

        if not self.claude_jsonl_path:
            return

        # Monitor the file
        while self.running:
            try:
                with open(self.claude_jsonl_path, "r") as f:
                    if self.skip_existing_entries:
                        f.seek(0, os.SEEK_END)
                        self.log(
                            "[INFO] Skipping existing Claude JSONL entries due to resume"
                        )
                        self.skip_existing_entries = False
                    else:
                        f.seek(0)  # Start from beginning when not resuming

                    self.log(
                        f"[INFO] Monitoring JSONL file: {self.claude_jsonl_path.name}"
                    )

                    while self.running:
                        # Check for session reset
                        if self.reset_handler.is_reset_pending():
                            self.log(
                                "[INFO] Session reset pending, waiting for new JSONL file..."
                            )

                            project_dir = self.get_project_log_dir()

                            if project_dir:
                                # Look for new session file
                                new_jsonl_path = (
                                    self.reset_handler.find_reset_session_file(
                                        project_dir=project_dir,
                                        current_file=self.claude_jsonl_path,
                                        max_wait=10.0,
                                    )
                                )
                            else:
                                new_jsonl_path = None
                                self.log("[WARNING] Could not get project directory")

                            if new_jsonl_path:
                                old_path = self.claude_jsonl_path.name
                                self.claude_jsonl_path = new_jsonl_path
                                self.log(
                                    f"[INFO] ✅ Switched from {old_path} to {new_jsonl_path.name}"
                                )

                                # Reset the handler state
                                self.reset_handler.clear_reset_state()

                                # Break out of inner loop to reopen with new file
                                break
                            else:
                                # Couldn't find new file, continue with current
                                self.log(
                                    "[WARNING] Could not find new session file, continuing with current"
                                )
                                self.reset_handler.clear_reset_state()

                        # Read next line from current file
                        line = f.readline()
                        if line:
                            try:
                                data = json.loads(line.strip())
                                # Process directly
                                self._process_entry(data)
                            except json.JSONDecodeError:
                                pass
                        else:
                            # Check if file still exists
                            if not self.claude_jsonl_path.exists():
                                self.log(
                                    "[WARNING] Current JSONL file no longer exists"
                                )
                                break
                            time.sleep(0.1)

            except Exception as e:
                self.log(f"[ERROR] Error monitoring Claude JSONL: {e}")
                # If we hit an error, wait a bit before retrying
                time.sleep(1)

    def _process_entry(self, data: Dict[str, Any]) -> None:
        """Process a single JSONL log entry.

        Args:
            data: Parsed JSON data from log entry
        """
        try:
            msg_type = data.get("type")

            # Handle "progress" type entries (newer JSONL format)
            # These have nested messages at data.message
            if msg_type == "progress":
                nested_data = data.get("data", {})
                nested_message = nested_data.get("message", {})
                nested_type = nested_message.get("type")

                # Skip messages from subtasks
                is_subtask = data.get("isSidechain")
                if is_subtask and (nested_type == "assistant" or nested_type == "user"):
                    return

                # Process based on nested message type
                if nested_type == "user":
                    self._process_user_entry(nested_message)
                elif nested_type == "assistant":
                    self._process_assistant_entry(nested_message)
                return

            # Handle direct message types (older JSONL format)
            # Skip messages from subtasks
            is_subtask = data.get("isSidechain")
            if is_subtask and (msg_type == "assistant" or msg_type == "user"):
                return

            if msg_type == "user":
                self._process_user_entry(data)
            elif msg_type == "assistant":
                self._process_assistant_entry(data)
            elif msg_type == "summary":
                self._process_summary_entry(data)

        except Exception as e:
            self.log(f"[ERROR] Error processing Claude log entry: {e}")

    def _process_user_entry(self, data: Dict[str, Any]) -> None:
        """Process a user message entry."""
        # Skip meta messages
        if data.get("isMeta", False):
            return

        message = data.get("message", {})
        content = message.get("content", "")

        # Handle both string content and structured content blocks
        if isinstance(content, str) and content:
            # Skip empty command output
            if content.strip() == "<local-command-stdout></local-command-stdout>":
                return

            # Check for command messages and extract the actual command
            if "<command-name>" in content:
                command_match = re.search(
                    r"<command-name>(.*?)</command-name>", content
                )
                args_match = re.search(r"<command-args>(.*?)</command-args>", content)

                if command_match:
                    command = command_match.group(1).strip()
                    args = args_match.group(1).strip() if args_match else ""
                    content = f"{command} {args}".strip()

            # Process user message (this will send to Vicoa if not from web)
            if self.message_queue is not None:
                self.message_processor.process_user_message(
                    content=content,
                    from_web=False,  # Message from CLI
                    input_queue=self.message_queue,
                )

        elif isinstance(content, list):
            # Handle structured content (e.g., tool results)
            formatted_parts = []
            for block in content:
                if isinstance(block, dict):
                    formatted_content = format_content_block(block)
                    if formatted_content:
                        formatted_parts.append(formatted_content)

    def _process_assistant_entry(self, data: Dict[str, Any]) -> None:
        """Process an assistant message entry."""
        message = data.get("message", {})
        content_blocks = message.get("content", [])
        formatted_parts = []
        tools_used = []

        for block in content_blocks:
            if isinstance(block, dict):
                formatted_content = format_content_block(block)
                if formatted_content:
                    formatted_parts.append(formatted_content)
                    # Track if this was a tool use
                    if block.get("type") == "tool_use":
                        tools_used.append(formatted_content)

        # Process message if we have content
        if formatted_parts:
            message_content = "\n".join(formatted_parts)

            # Send to Vicoa via message processor
            queued_responses = self.message_processor.process_assistant_message(
                content=message_content,
                tools_used=tools_used,
                send_message_lock=self.send_message_lock,
                requested_input_messages=self.requested_input_messages,
                pending_permission_options=self.pending_permission_options,
            )

            # Queue any user responses from web UI
            if queued_responses and self.message_queue:
                for response in queued_responses:
                    self.message_queue.append(response)

    def _process_summary_entry(self, data: Dict[str, Any]) -> None:
        """Process a summary entry (session started)."""
        pass

    def __enter__(self):
        """Context manager entry."""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop()
        return False
