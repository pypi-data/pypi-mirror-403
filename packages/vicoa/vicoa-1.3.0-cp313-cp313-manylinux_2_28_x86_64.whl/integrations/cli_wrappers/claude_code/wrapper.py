"""New modular Claude Code wrapper.

This is the main orchestrator that composes all refactored modules
into a cohesive wrapper implementation.
"""

import argparse
import logging
import os
import select
import sys
import threading
import time
import uuid
from pathlib import Path
from typing import Optional, TextIO

from vicoa.utils import get_project_path

from .config import ClaudeWrapperConfig, VICOA_WRAPPER_LOG_DIR
from .detection import (
    PermissionDetector,
    PlanDetector,
    QuestionDetector,
    ControlDetector,
)
from .messaging import MessageProcessor, MessageQueue, InputRequestManager
from .monitoring import HeartbeatManager, JSONLMonitor
from .session_reset_handler import SessionResetHandler
from .state import SessionState, ToggleManager
from .terminal import ANSICleaner, TerminalBuffer, PTYManager
from .utils import find_claude_cli, InputHandler
from integrations.utils.git_utils import GitDiffTracker
from vicoa.sdk.async_client import AsyncVicoaClient
from vicoa.sdk.client import VicoaClient


class ClaudeWrapper:
    """Modular Claude Code wrapper using composition.

    This wrapper composes specialized modules to provide a clean,
    maintainable architecture that's easy to modify when Claude CLI changes.
    """

    def __init__(self, config: ClaudeWrapperConfig):
        """Initialize wrapper with configuration.

        Args:
            config: Wrapper configuration
        """
        self.config = config
        self.running = True

        # Setup logging
        self.debug_log_file: Optional[TextIO] = None
        self._init_logging()

        # Initialize Vicoa clients
        self.vicoa_client_sync: Optional[VicoaClient] = None
        self.vicoa_client_async: Optional[AsyncVicoaClient] = None
        self._init_vicoa_clients()

        # Initialize git tracking
        self.git_tracker: Optional[GitDiffTracker] = None
        self._init_git_tracker()

        # Initialize terminal management
        self.pty_manager = PTYManager(log_func=self.log)
        self.terminal_buffer = TerminalBuffer(max_size=config.terminal_buffer_max_size)
        self.ansi_cleaner = ANSICleaner()

        # Initialize detectors
        # Order matters: more specific detectors should come first
        # PlanDetector is more specific than PermissionDetector for "Would you like to proceed" prompts
        from collections import OrderedDict

        self.detectors = OrderedDict(
            [
                ("plan", PlanDetector()),
                ("permission", PermissionDetector()),
                ("question", QuestionDetector()),
                ("control", ControlDetector()),
            ]
        )

        # Initialize state management
        self.session_state = SessionState(
            is_resuming=config.is_resuming,
            idle_delay=config.idle_delay,
            terminal_buffer=self.terminal_buffer,
        )
        self.toggle_manager = ToggleManager(
            initial_permission_mode=config.permission_mode,
            write_to_pty_func=self.pty_manager.write_to_pty,
            log_func=self.log,
        )

        # Initialize messaging
        self.message_queue = MessageQueue()
        self.message_processor = MessageProcessor(
            agent_instance_id=config.agent_instance_id,
            agent_name=config.name,
            vicoa_client=self.vicoa_client_sync,
            git_tracker=self.git_tracker,
            log_func=self.log,
        )

        # Session reset handler
        self.reset_handler = SessionResetHandler(log_func=self.log)

        # Initialize monitoring
        self.heartbeat = HeartbeatManager(
            agent_instance_id=config.agent_instance_id,
            base_url=config.base_url,
            vicoa_client=self.vicoa_client_sync,
            interval=config.heartbeat_interval,
            log_func=self.log,
        )
        # Input handler
        self.input_handler = InputHandler()

        # Threading
        self.send_message_lock = threading.Lock()
        self.requested_input_messages: set[str] = set()
        self.last_pty_output_time: float = 0.0

        # Prompt checking optimization
        self._prompt_check_start_time: Optional[float] = None
        self._last_checked_buffer_size: int = 0
        self._last_prompt_check_time: float = 0.0

        # Initialize JSONL monitor with all dependencies
        self.jsonl_monitor = JSONLMonitor(
            agent_instance_id=config.agent_instance_id,
            message_processor=self.message_processor,
            reset_handler=self.reset_handler,
            log_func=self.log,
            skip_existing_entries=config.is_resuming,
            message_queue=self.message_queue,
            send_message_lock=self.send_message_lock,
            requested_input_messages=self.requested_input_messages,
            pending_permission_options=self.session_state.pending_permission_options,
        )

        # Initialize input request manager
        self.input_request_manager = InputRequestManager(
            agent_instance_id=config.agent_instance_id,
            agent_name=config.name,
            vicoa_client_async=self.vicoa_client_async,
            vicoa_client_sync=self.vicoa_client_sync,
            message_processor=self.message_processor,
            message_queue=self.message_queue,
            session_state=self.session_state,
            toggle_manager=self.toggle_manager,
            pty_manager=self.pty_manager,
            log_func=self.log,
        )

    def run(self) -> int:
        """Main entry point - run the wrapper.

        Returns:
            Exit code (0 for success, 1 for error)
        """
        try:
            self._setup()
            self._run_event_loop()
            return 0
        except KeyboardInterrupt:
            self.log("[INFO] Interrupted by user")
            return 0
        except Exception as e:
            self.log(f"[ERROR] Fatal error: {e}")
            import traceback

            self.log(traceback.format_exc())
            return 1
        finally:
            self._cleanup()

    def _setup(self) -> None:
        """Setup before main loop."""
        self.log("[INFO] Setting up Vicoa...")
        # Register agent instance only if starting a new session
        if self.config.is_resuming:
            self.log(f"[INFO] Resuming session: {self.config.agent_instance_id}")
        else:
            if self.vicoa_client_sync:
                try:
                    registration = self.vicoa_client_sync.register_agent_instance(
                        agent_type=self.config.name,
                        transport="local",
                        agent_instance_id=self.config.agent_instance_id,
                        name=None,
                        project=get_project_path(),
                        home_dir=str(Path.home()),
                    )
                    # Update agent_instance_id from registration response
                    self.config.agent_instance_id = registration.agent_instance_id

                    # Update all components with the new agent_instance_id
                    self.message_processor.agent_instance_id = (
                        self.config.agent_instance_id
                    )
                    self.heartbeat.agent_instance_id = self.config.agent_instance_id
                    self.jsonl_monitor.agent_instance_id = self.config.agent_instance_id

                    # Create initial session message
                    response = self.vicoa_client_sync.send_message(
                        content=f"{self.config.name} session started, waiting for your input...",
                        agent_type=self.config.name,
                        agent_instance_id=self.config.agent_instance_id,
                        requires_user_input=False,
                    )

                    # Set the initial message ID so idle_monitor_loop can request input
                    if response and hasattr(response, "message_id"):
                        self.message_processor.last_message_id = response.message_id
                        self.message_processor.last_message_time = time.time()
                    else:
                        self.log(
                            "[WARNING] Initial session message sent but no message_id received"
                        )

                    # Process any queued user messages from the response
                    if (
                        response
                        and hasattr(response, "queued_user_messages")
                        and response.queued_user_messages
                    ):
                        for queued_msg in response.queued_user_messages:
                            self.message_queue.append(queued_msg)
                except Exception as e:
                    self.log(f"[ERROR] Failed to register agent instance: {e}")
                    # Continue anyway - wrapper can still function locally

        # Start heartbeat
        self.heartbeat.start()

        # Start JSONL monitor
        self.jsonl_monitor.start()

        # Start input request manager
        self.input_request_manager.start()

        # Start PTY
        self._start_claude_pty()

    def _start_claude_pty(self) -> None:
        """Start Claude CLI in PTY."""
        claude_path = find_claude_cli()

        # Build command
        cmd = self._build_claude_command(claude_path)

        # Create PTY
        env = {"CLAUDE_CODE_ENTRYPOINT": "jsonlog-wrapper"}
        self.pty_manager.create_pty(cmd, env)
        self.pty_manager.set_raw_mode()

    def _build_claude_command(self, claude_path: str) -> list:
        """Build Claude CLI command with arguments."""
        if self.config.is_resuming:
            cmd = [claude_path, "--resume", self.config.agent_instance_id]
        else:
            cmd = [claude_path, "--session-id", self.config.agent_instance_id]

        if self.config.permission_mode:
            cmd.extend(["--permission-mode", self.config.permission_mode])

        if self.config.dangerously_skip_permissions:
            cmd.append("--dangerously-skip-permissions")

        return cmd

    def _run_event_loop(self) -> None:
        """Main event loop."""
        while self.running:
            try:
                # Check for input from stdin or PTY
                rlist, _, _ = select.select(
                    [sys.stdin, self.pty_manager.master_fd], [], [], 0.01
                )

                # Handle PTY output
                if self.pty_manager.master_fd in rlist:
                    self._handle_pty_output()

                # Handle stdin input
                if sys.stdin in rlist:
                    self._handle_stdin_input()

                # Process queued messages
                if self.message_queue:
                    self._process_queued_message()

                # Check for prompts in terminal buffer (only when conditions warrant)
                if self._should_check_for_prompts():
                    self._check_for_prompts()

            except Exception as e:
                self.log(f"[ERROR] Error in event loop: {e}")
                import traceback

                self.log(traceback.format_exc())

    def _handle_pty_output(self) -> None:
        """Handle output from Claude CLI."""
        try:
            data = self.pty_manager.read_from_pty()
            if data:
                self.last_pty_output_time = time.time()
                # Write to stdout
                sys.stdout.buffer.write(data)
                sys.stdout.buffer.flush()

                # Add to buffer
                text = data.decode("utf-8", errors="replace")
                self.terminal_buffer.append(text)

                # Mark terminal activity whenever we receive output
                # The idle check will use buffer content to distinguish
                # between real work and status line updates
                self.session_state.mark_terminal_activity()

                # Detect local toggle changes and sync to UI
                # Only check if text contains relevant keywords (matching v2_0 optimization)
                text_lower = text.lower()
                if (
                    "shift+tab" in text_lower
                    or "tab to toggle" in text_lower
                    or "? for shortcut" in text_lower
                ):
                    # Only clean ANSI when we need to check toggle state
                    clean_text = self.ansi_cleaner.clean_csi_sequences(text)
                    feedback_messages = self.toggle_manager.update_from_terminal(
                        clean_text
                    )
                    for message in feedback_messages:
                        self._send_feedback_message(message)

                # Track interrupts for idle detection
                # Check for "esc to interrupt" or "ctrl+b to run in background" text
                # (not just the escape byte, which appears in ANSI codes)
                if (
                    "esc to interrupt" in text_lower
                    or "ctrl+b to run in background" in text_lower
                    or "esc to cancel" in text_lower
                ):
                    self.session_state.mark_interrupt()
            else:
                # Empty data means child process has exited
                self.log(
                    "[INFO] Claude process exited (empty read), shutting down wrapper"
                )
                self.running = False

        except OSError as e:
            # OSError during read typically means the child process has exited
            self.log(
                f"[INFO] Claude process exited (OSError: {e}), shutting down wrapper"
            )
            self.running = False
        except Exception as e:
            self.log(f"[ERROR] Error reading PTY: {e}")
            # Don't set running = False for other exceptions

    def _handle_stdin_input(self) -> None:
        """Handle input from stdin."""
        try:
            char = os.read(sys.stdin.fileno(), 1)
            if char:
                # Check for Ctrl+Z
                if char == b"\x1a":
                    self.pty_manager.suspend_for_ctrl_z()
                    return

                # Write to PTY
                self.pty_manager.write_to_pty(char)

                # Process through input handler
                # JSONL monitor handles forwarding to Vicoa to avoid duplicates.
                self.input_handler.process_char(char)

        except Exception as e:
            self.log(f"[ERROR] Error reading stdin: {e}")

    def _should_check_for_prompts(self) -> bool:
        """Determine if we should check for prompts.

        This mimics v2_0 logic: only check when tool was used and Claude is idle,
        with proper settling time. This prevents expensive ANSI cleaning and regex
        operations from running on every event loop iteration.

        Returns:
            True if conditions warrant checking for prompts, False otherwise
        """
        # Don't check if we're processing a queued message
        if self.message_queue:
            return False

        # Check if we're in a state where prompts might appear
        # This matches v2_0: after tool use AND when idle
        if (
            self.message_processor.last_was_tool_use
            and self.session_state.is_claude_idle()
        ):
            # Start timing if we haven't already
            if self._prompt_check_start_time is None:
                self._prompt_check_start_time = time.time()
                return False

            # Wait 0.5s for prompt to settle (matching v2_0 behavior)
            if time.time() - self._prompt_check_start_time < 0.5:
                return False

            # Debounce: don't check too frequently if buffer unchanged
            current_size = self.terminal_buffer.size()
            time_since_last_check = time.time() - self._last_prompt_check_time

            # Skip if buffer unchanged and checked recently (within 100ms)
            if (
                current_size == self._last_checked_buffer_size
                and time_since_last_check < 0.1
            ):
                return False

            return True
        else:
            # Reset timing when conditions change
            self._prompt_check_start_time = None
            return False

    def _check_for_prompts(self) -> None:
        """Check terminal buffer for prompts that need handling."""
        # Update tracking for optimization
        self._last_checked_buffer_size = self.terminal_buffer.size()
        self._last_prompt_check_time = time.time()

        # Clean buffer for parsing
        clean_buffer = self.ansi_cleaner.clean_all(self.terminal_buffer.get())

        # Check each detector
        for detector_name, detector in self.detectors.items():
            result = detector.detect_and_extract(clean_buffer)
            if result.detected:
                # Debounce prompt handling to allow terminal output to settle
                if time.time() - self.last_pty_output_time < 0.3:
                    break

                # Ensure data is present (should always be true when detected=True)
                if not result.data:
                    self.log(
                        f"[WARNING] Detector {detector_name} detected but returned no data"
                    )
                    break

                signature = self._build_prompt_signature(detector_name, result.data)
                if not self.session_state.should_send_prompt(signature):
                    break
                self._handle_detected_prompt(detector_name, result.data)
                self.session_state.mark_prompt_sent(signature)

                # Clear buffer to prevent re-processing the same prompt
                self.terminal_buffer.clear()
                self._last_checked_buffer_size = 0

                break  # Handle one prompt at a time
        else:
            # No prompt detected, reset signature gate
            self.session_state.clear_prompt_signature()

    def _handle_detected_prompt(self, prompt_type: str, data: dict) -> None:
        """Handle a detected prompt.

        Args:
            prompt_type: Type of prompt detected
            data: Extracted data from detector
        """
        if prompt_type == "control":
            # Handle control command (legacy format from detector)
            self._handle_control_command_from_dict(data)
        else:
            # Handle user input prompt (permission, plan, question)
            self._handle_input_prompt(data)
            self.session_state.mark_prompt_detected(prompt_type)

    def _handle_control_command_from_dict(self, data: dict) -> None:
        """Handle a control command from dict (legacy format from detector).

        Note: This is for backwards compatibility. New code should use
        the JSON string format handled by _handle_control_command().
        """
        control = data.get("control_command", {})
        setting = control.get("setting")

        if setting == "interrupt":
            # Send escape key
            self.pty_manager.write_to_pty(b"\x1b")
            self.message_queue.clear()

        elif setting in self.toggle_manager.get_all_settings():
            # Handle toggle setting
            value = control.get("value")
            target = self.toggle_manager.normalize_value(setting, value)
            if target:
                self.toggle_manager.set_toggle(setting, target)

    def _handle_input_prompt(self, data: dict) -> None:
        """Handle an input prompt (permission, plan, question)."""
        question = data.get("question", "")
        options = data.get("options", [])
        options_map = self._normalize_options_map(
            data.get("options_map") or {}, options
        )

        # Store pending options so UI selections can be converted to numbers
        if options_map:
            self.session_state.set_pending_permission_options(options_map)

        # Send to Vicoa as requires_user_input message
        if self.vicoa_client_sync and self.config.agent_instance_id:
            try:
                # Format message with options
                if options:
                    options_text = "\n".join(options)
                    message = f"{question}\n\n[OPTIONS]\n{options_text}\n[/OPTIONS]"
                else:
                    message = question

                response = self.vicoa_client_sync.send_message(
                    content=message,
                    agent_type=self.config.name,
                    agent_instance_id=self.config.agent_instance_id,
                    requires_user_input=False,
                )

                if response and hasattr(response, "message_id"):
                    self.message_processor.last_message_id = response.message_id
                    self.message_processor.last_message_time = time.time()
                    # Allow input requests to flow for prompt responses
                    self.message_processor.last_was_tool_use = False
                    # Let idle detection handle input requests naturally

            except Exception as e:
                self.log(f"[ERROR] Failed to send prompt to Vicoa: {e}")

    def _normalize_options_map(
        self, options_map: dict, options: list[str]
    ) -> dict[str, str]:
        """Normalize option mapping to a text -> number map."""
        if not options_map and not options:
            return {}

        # If keys are numbers, invert using option text
        if options_map and all(
            str(key).strip().isdigit() for key in options_map.keys()
        ):
            inverted = {}
            for number, text in options_map.items():
                text = str(text).strip()
                if text:
                    inverted[text] = str(number).strip()
                    if ". " in text:
                        _, stripped = text.split(". ", 1)
                        stripped = stripped.strip()
                        if stripped:
                            inverted[stripped] = str(number).strip()
            return inverted

        # Build from options list if needed
        normalized = dict(options_map)
        for option in options or []:
            option_text = str(option).strip()
            if not option_text:
                continue
            if ". " in option_text:
                number, text = option_text.split(". ", 1)
                number = number.strip()
                text = text.strip()
                if number.isdigit() and text:
                    normalized[text] = number
                    normalized[option_text] = number
        return normalized

    def _build_prompt_signature(self, prompt_type: str, data: dict) -> str:
        """Build a stable signature for de-duplicating prompt sends."""
        question = (data.get("question") or "").strip()
        options = data.get("options") or []
        options_sig = "|".join(opt.strip() for opt in options if opt is not None)
        return f"{prompt_type}:{question}:{options_sig}"

    def _process_queued_message(self) -> None:
        """Process next message from queue."""
        if self.message_queue.is_empty():
            return

        try:
            content = self.message_queue.popleft()

            # Defense in depth: Filter control commands before sending to Claude
            # (Primary filtering happens in _process_user_responses, this catches edge cases)
            try:
                if self.input_request_manager._handle_control_command(content):
                    return
            except Exception as e:
                self.log(
                    f"[WARNING] Error checking control command: {e}, continuing..."
                )

            # Check if this is a permission prompt response
            if self.session_state.pending_permission_options:
                content_stripped = content.strip()
                options_map = self.session_state.pending_permission_options
                matched = False

                if content_stripped in options_map:
                    converted = options_map[content_stripped]
                    content = converted
                    matched = True
                else:
                    lowered = content_stripped.lower()
                    for key, value in options_map.items():
                        if key.strip().lower() == lowered:
                            content = value
                            matched = True
                            break

                if not matched and content_stripped.isdigit():
                    if content_stripped in options_map.values():
                        content = content_stripped
                        matched = True

                # Always clear the mapping after handling a permission response
                self.session_state.clear_pending_permission_options()
                self.terminal_buffer.clear()
                self.session_state.clear_prompt_timing()
                self.session_state.clear_prompt_signature()
                # Clear last_was_tool_use for ANY prompt type (permission, plan, question)
                # This allows input requests to resume after user responds
                self.message_processor.last_was_tool_use = False
                self._prompt_check_start_time = None

            # Check for session reset commands from web UI
            if self.reset_handler.check_for_reset_command(content.strip()):
                self.reset_handler.mark_reset_detected(content.strip())

            # Send to Claude - send message content first
            self.pty_manager.write_to_pty(content.encode("utf-8"))
            time.sleep(0.25)  # Wait a bit for Claude to process

            # Clear state when user sends input
            # NOTE: We do NOT update last_message_time - that only tracks Claude's output
            # NOTE: We keep last_message_id so idle detection can work - JSONL monitor will update it
            self.message_processor.pending_input_message_id = None

            # Send carriage return (Enter key) to submit
            self.pty_manager.write_to_pty(b"\r")

            # Don't immediately request input here - let the normal flow handle it:
            # - If Claude is busy: control poller will pick up messages
            # - If Claude is idle: idle detection will request input after minimum delay
            # This prevents unwanted push notifications (Use Case #5)

        except Exception as e:
            self.log(f"[ERROR] Failed to process queued message: {e}")

    def _cleanup(self) -> None:
        """Cleanup before exit."""
        self.running = False

        # Stop input request manager
        self.input_request_manager.stop()

        # Stop heartbeat
        self.heartbeat.stop()

        # Stop JSONL monitor
        self.jsonl_monitor.stop()

        # Close PTY
        self.pty_manager.close()

        # End session with Vicoa
        if self.vicoa_client_sync and self.config.agent_instance_id:
            try:
                self.vicoa_client_sync.end_session(self.config.agent_instance_id)
            except Exception as e:
                self.log(f"[ERROR] Failed to end session: {e}")

        # Close Vicoa clients
        if self.vicoa_client_sync:
            try:
                self.vicoa_client_sync.close()
            except Exception as e:
                self.log(f"[ERROR] Failed to close sync client: {e}")

        if self.vicoa_client_async:
            try:
                import asyncio

                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(self.vicoa_client_async.close())
                loop.close()
            except Exception as e:
                self.log(f"[ERROR] Failed to close async client: {e}")

        # Close log file
        if self.debug_log_file:
            try:
                self.log("=== Claude Wrapper (Modular) Log Ended ===")
                self.debug_log_file.flush()
                self.debug_log_file.close()
            except Exception:
                pass

    def _init_logging(self) -> None:
        """Initialize debug logging."""
        try:
            VICOA_WRAPPER_LOG_DIR.mkdir(exist_ok=True, parents=True)
            log_file_path = (
                VICOA_WRAPPER_LOG_DIR / f"{self.config.agent_instance_id}.log"
            )
            self.debug_log_file = open(log_file_path, "w")
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
            milliseconds = int((time.time() % 1) * 1000)
            self.log(
                f"=== Claude Wrapper (Modular) - {timestamp}.{milliseconds:03d} ==="
            )
        except Exception as e:
            print(f"Failed to create debug log file: {e}", file=sys.stderr)

    def _init_vicoa_clients(self) -> None:
        """Initialize Vicoa SDK clients."""
        if not self.config.api_key:
            raise ValueError("API key is required to initialize Vicoa clients")

        self.vicoa_client_sync = VicoaClient(
            api_key=self.config.api_key,
            base_url=self.config.base_url,
            max_retries=1440,
            backoff_factor=1.0,
            backoff_max=60.0,
            log_func=self.log,
        )

        self.vicoa_client_async = AsyncVicoaClient(
            api_key=self.config.api_key,
            base_url=self.config.base_url,
            max_retries=1440,
            backoff_factor=1.0,
            backoff_max=60.0,
            log_func=self.log,
        )

    def _send_feedback_message(self, message: str) -> None:
        """Send a status update to Vicoa about local control actions."""
        if not self.vicoa_client_sync or not self.config.agent_instance_id:
            self.log(
                "[WARNING] Cannot send feedback: vicoa_client_sync or agent_instance_id not initialized"
            )
            return

        try:
            response = self.vicoa_client_sync.send_message(
                content=message,
                agent_type=self.config.name,
                agent_instance_id=self.config.agent_instance_id,
                requires_user_input=False,
            )
            if response and getattr(response, "queued_user_messages", None):
                for queued in response.queued_user_messages:
                    self.message_processor.process_user_message_sync(
                        queued, from_web=True
                    )
                    self.message_queue.append(queued)
        except Exception as e:
            self.log(f"[ERROR] Failed to send feedback message '{message}': {e}")

    def _init_git_tracker(self) -> None:
        """Initialize git diff tracking."""
        if not self.config.enable_git_tracking:
            return

        try:
            # Create a logger that routes to our debug log
            git_logger = logging.getLogger("ClaudeWrapper.GitTracker")
            git_logger.setLevel(logging.DEBUG)

            class LogHandler(logging.Handler):
                def __init__(self, log_func):
                    super().__init__()
                    self.log_func = log_func

                def emit(self, record):
                    msg = self.format(record)
                    level = record.levelname
                    self.log_func(f"[{level}] {msg}")

            handler = LogHandler(self.log)
            handler.setFormatter(logging.Formatter("%(message)s"))
            git_logger.addHandler(handler)
            git_logger.propagate = False

            self.git_tracker = GitDiffTracker(enabled=True, logger=git_logger)
        except Exception as e:
            self.log(f"[WARNING] Failed to initialize git tracker: {e}")
            self.git_tracker = None

    def log(self, message: str) -> None:
        """Write to debug log file."""
        if self.debug_log_file:
            try:
                timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
                milliseconds = int((time.time() % 1) * 1000)
                self.debug_log_file.write(
                    f"[{timestamp}.{milliseconds:03d}] {message}\n"
                )
                self.debug_log_file.flush()
            except Exception:
                pass


def main() -> int:
    """Main entry point for modular wrapper.

    Returns:
        Exit code (0 for success, 1 for error)
    """
    parser = argparse.ArgumentParser(description="Claude Code Wrapper (Modular)")
    parser.add_argument("--api-key", help="Vicoa API key")
    parser.add_argument("--base-url", default=None, help="Vicoa base URL")
    parser.add_argument("--permission-mode", help="Initial permission mode")
    parser.add_argument("--dangerously-skip-permissions", action="store_true")
    parser.add_argument("--name", default="Claude Code", help="Agent display name")
    parser.add_argument("--agent-instance-id", help="Agent instance ID")
    parser.add_argument("--resume", help="Resume session ID")
    args = parser.parse_args()

    # Use resume as agent_instance_id if provided
    agent_instance_id = args.resume or args.agent_instance_id or str(uuid.uuid4())
    is_resuming = bool(args.resume)

    config = ClaudeWrapperConfig.from_args(
        api_key=args.api_key,
        base_url=args.base_url,
        permission_mode=args.permission_mode,
        dangerously_skip_permissions=args.dangerously_skip_permissions,
        name=args.name,
        agent_instance_id=agent_instance_id,
        is_resuming=is_resuming,
    )

    wrapper = ClaudeWrapper(config)
    return wrapper.run()


if __name__ == "__main__":
    sys.exit(main())
