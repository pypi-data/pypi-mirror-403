"""Async input request management for Claude Code Wrapper.

This module handles asynchronous input requests from the Vicoa web UI,
including idle detection, long-polling, and control command processing.
"""

import asyncio
import json
import threading
from typing import Callable, Optional, Set, TYPE_CHECKING

if TYPE_CHECKING:
    from vicoa.sdk.async_client import AsyncVicoaClient
    from .processor import MessageProcessor
    from .queue_manager import MessageQueue
    from ..state.session_state import SessionState
    from ..state.toggle_manager import ToggleManager
    from ..terminal.pty_manager import PTYManager
from ..config import CONTROL_JSON_PATTERN


class InputRequestManager:
    """Manages async input requests from Vicoa web UI.

    This class handles:
    - Idle monitoring loop
    - Long-polling for user responses
    - Control command processing
    - Feedback message sending
    """

    def __init__(
        self,
        agent_instance_id: str,
        agent_name: str,
        vicoa_client_async: Optional["AsyncVicoaClient"],
        vicoa_client_sync,  # VicoaClient
        message_processor: "MessageProcessor",
        message_queue: "MessageQueue",
        session_state: "SessionState",
        toggle_manager: "ToggleManager",
        pty_manager: "PTYManager",
        log_func: Callable[[str], None],
    ):
        """Initialize input request manager.

        Args:
            agent_instance_id: Agent instance ID
            agent_name: Agent display name
            vicoa_client_async: Async Vicoa client for long-polling
            vicoa_client_sync: Sync Vicoa client for feedback messages
            message_processor: Message processor instance
            message_queue: Message queue for queuing responses to CLI
            session_state: Session state manager
            toggle_manager: Toggle manager for control settings
            pty_manager: PTY manager for sending interrupts
            log_func: Logging function
        """
        self.agent_instance_id = agent_instance_id
        self.agent_name = agent_name
        self.vicoa_client_async = vicoa_client_async
        self.vicoa_client_sync = vicoa_client_sync
        self.message_processor = message_processor
        self.message_queue = message_queue
        self.session_state = session_state
        self.toggle_manager = toggle_manager
        self.pty_manager = pty_manager
        self.log = log_func

        # State
        self.running = True
        self.async_loop: Optional[asyncio.AbstractEventLoop] = None
        self.async_thread: Optional[threading.Thread] = None
        self.requested_input_messages: Set[str] = set()
        self.pending_input_task: Optional[asyncio.Task] = None
        self.control_poller_task: Optional[asyncio.Task] = None

    def start(self) -> None:
        """Start the async input request loop in a separate thread."""

        def run_async_loop():
            try:
                self.async_loop = asyncio.new_event_loop()
                asyncio.set_event_loop(self.async_loop)
                self.async_loop.run_until_complete(self.idle_monitor_loop())
            except (KeyboardInterrupt, RuntimeError):
                # RuntimeError happens when loop.stop() is called
                pass
            except Exception as e:
                self.log(f"[ERROR] Error in async loop: {e}")

        self.async_thread = threading.Thread(target=run_async_loop, daemon=True)
        self.async_thread.start()

    def stop(self) -> None:
        """Stop the async input request loop."""
        self.running = False

        # Cancel tasks
        if self.async_loop:
            if self.control_poller_task and not self.control_poller_task.done():
                self.async_loop.call_soon_threadsafe(self.control_poller_task.cancel)
            if self.pending_input_task and not self.pending_input_task.done():
                self.async_loop.call_soon_threadsafe(self.pending_input_task.cancel)

        if self.async_loop and self.async_loop.is_running():
            self.async_loop.call_soon_threadsafe(self.async_loop.stop)

    def request_input_now(self, message_id: str) -> None:
        """Request user input immediately for a specific message."""
        if not self.async_loop or not self.async_loop.is_running():
            self.log("[WARNING] Async loop not running; cannot request input now")
            return

        def _schedule():
            # Skip if already requested
            if message_id in self.requested_input_messages:
                return
            self.requested_input_messages.add(message_id)
            self.message_processor.mark_input_requested(message_id)
            self.cancel_pending_input_request()
            self.pending_input_task = asyncio.create_task(
                self.request_user_input_async(message_id)
            )

        self.async_loop.call_soon_threadsafe(_schedule)

    def cancel_pending_input_request(self) -> None:
        """Cancel any pending input request task."""
        if self.pending_input_task and not self.pending_input_task.done():
            self.pending_input_task.cancel()

    async def idle_monitor_loop(self):
        """Async loop to monitor idle state and request input."""
        if not self.vicoa_client_async:
            self.log("[ERROR] Vicoa async client not initialized")
            return

        # Ensure async client session
        await self.vicoa_client_async._ensure_session()

        # Start control command poller in background
        self.control_poller_task = asyncio.create_task(self.control_command_poller())

        while self.running:
            await asyncio.sleep(0.5)  # Check every 500ms

            # Check if we should request input
            message_id = self.message_processor.should_request_input(
                is_claude_idle_func=self.session_state.is_claude_idle
            )

            if message_id:
                # Skip if we've already requested input for this message
                if message_id in self.requested_input_messages:
                    continue

                # Track that we've requested input for this message
                self.requested_input_messages.add(message_id)

                # Mark as requested
                self.message_processor.mark_input_requested(message_id)

                # Cancel any existing task
                self.cancel_pending_input_request()

                # Start new input request task
                self.pending_input_task = asyncio.create_task(
                    self.request_user_input_async(message_id)
                )

    async def request_user_input_async(self, message_id: str):
        """Async task to request user input from web UI.

        This method long-polls for user responses and processes them. Control commands
        (like permission mode changes) are handled but don't count as "actual input",
        allowing immediate subsequent requests without blocking.

        Args:
            message_id: The message ID to request input for
        """
        has_actual_input = False

        try:
            if not self.vicoa_client_async:
                self.log("[ERROR] Vicoa async client not initialized")
                return

            # Ensure async client session exists
            await self.vicoa_client_async._ensure_session()

            # Long-polling request for user input (blocks until user responds)
            user_responses = await self.vicoa_client_async.request_user_input(
                message_id=message_id,
                timeout_minutes=1440,  # 24 hours
                poll_interval=3.0,
            )

            # Process responses and check if we got actual input vs control commands
            has_actual_input = self._process_user_responses(user_responses)

        except asyncio.CancelledError:
            self.log(f"[INFO] request_user_input cancelled for message {message_id}")
            raise

        except Exception as e:
            self.log(f"[ERROR] Failed to request user input: {e}")

            # Fallback: If message already requires input, create a new waiting message
            if "400" in str(e) and "already requires user input" in str(e):
                has_actual_input = await self._send_waiting_message_and_get_responses()

        finally:
            # State management for duplicate request prevention:
            # - If we got actual input: keep pending_input_message_id set (prevents duplicate requests)
            # - If only control commands: clear state to allow immediate subsequent requests
            if not has_actual_input:
                self.message_processor.pending_input_message_id = None
                # Don't reset last_input_request_time - let normal idle detection handle it

            # Always clear from tracking set to allow retries if needed
            self.requested_input_messages.discard(message_id)

    def _process_user_responses(self, responses: list[str]) -> bool:
        """Process user responses and queue non-control messages for Claude.

        Args:
            responses: List of user response strings from web UI

        Returns:
            True if any actual (non-control) input was queued, False if only control commands

        Note:
            Control commands (like permission mode changes) are handled but not queued.
            They won't be sent to Claude, allowing immediate subsequent requests.
        """
        has_actual_input = False

        for response in responses:
            # Always track the message for deduplication
            self.message_processor.process_user_message_sync(response, from_web=True)

            # Check if this is a control command (JSON format)
            if self._handle_control_command(response):
                continue

            # Queue actual user input for Claude
            self.message_queue.append(response)
            has_actual_input = True

        return has_actual_input

    async def _send_waiting_message_and_get_responses(self) -> bool:
        """Send a waiting message and get user responses (fallback for 400 errors).

        Returns:
            True if actual input was received, False if only control commands
        """
        try:
            if not self.vicoa_client_async:
                return False

            response = await self.vicoa_client_async.send_message(
                content="Waiting for your input...",
                agent_type=self.agent_name,
                agent_instance_id=self.agent_instance_id,
                requires_user_input=True,
                poll_interval=3.0,
            )

            # Process any queued responses
            return self._process_user_responses(response.queued_user_messages)

        except Exception as e:
            self.log(f"[ERROR] Failed to send waiting message: {e}")
            return False

    def _handle_control_command(self, content: str) -> bool:
        """Handle JSON control commands from the web UI.

        Expected formats:
        - Toggle: {"type": "control", "setting": "X", "value": "Y"}
        - Interrupt: {"type": "control", "setting": "interrupt"}
        - Hybrid: "Text description. {"type": "control", ...}"

        Returns: True if command was recognized (even if failed), False otherwise
        """
        try:
            control = self._parse_control_json(content)
            if not control:
                return False

            setting = control.get("setting", "").strip()
            if not setting:
                return False

            # Handle interrupt
            if setting == "interrupt":
                return self._handle_interrupt_action()

            # Handle toggle settings
            value = (control.get("value") or "").strip()
            if not value:
                self._send_feedback_message(f"Missing value for setting '{setting}'")
                return True

            # Delegate to toggle manager
            success = self.toggle_manager.handle_toggle_request(setting, value)

            # Only send feedback on failure
            # Success feedback will come from terminal detection when change is confirmed
            if not success:
                target_slug = self.toggle_manager.normalize_value(setting, value)
                if target_slug:
                    display_value = self.toggle_manager.humanize_value(
                        setting, target_slug
                    )
                else:
                    display_value = value
                self._send_feedback_message(
                    f"Failed to set {setting.replace('_', ' ')} to {display_value}"
                )

            return True

        except json.JSONDecodeError:
            return False
        except Exception as e:
            self.log(f"[ERROR] Error handling control command: {e}")
            return False

    def _parse_control_json(self, content: str) -> Optional[dict]:
        """Parse JSON control command from text (can be embedded).

        Supports both formats for backwards compatibility:
        - {"type": "control", "setting": "X", "value": "Y"}
        - {"type": "control", "action": "interrupt"}
        """
        if not content:
            return None

        match = CONTROL_JSON_PATTERN.search(content)
        if not match:
            return None

        json_str = match.group(0)
        try:
            data = json.loads(json_str)
        except json.JSONDecodeError:
            return None

        if not isinstance(data, dict) or data.get("type") != "control":
            return None

        # Support both "setting" (new format) and "action" (old format)
        setting = data.get("setting") or data.get("action")
        if not setting:
            return None

        value = data.get("value")
        if value is not None:
            return {"setting": str(setting), "value": str(value)}
        return {"setting": str(setting)}

    def _handle_interrupt_action(self) -> bool:
        """Handle interrupt action from web UI.

        Clears queued messages, sends Escape key to Claude Code,
        and sends confirmation feedback to user.

        Returns: True (command was handled)
        """
        # Clear all queued messages
        if len(self.message_queue) > 0:
            self.message_queue.clear()

        # Always send the escape key - if Claude is idle it won't hurt,
        # if Claude is busy it will interrupt. The user clicked "Stop" so
        # we should respect that regardless of our detection state.
        try:
            self.pty_manager.write_to_pty(b"\x1b")
        except Exception as e:
            self.log(f"[ERROR] Failed to send interrupt signal: {e}")
            self._send_feedback_message("Failed to interrupt Claude")
            return True

        # Cancel any pending input request since we're interrupting
        self.cancel_pending_input_request()

        # Clear the pending input message ID to allow new input requests
        self.message_processor.pending_input_message_id = None

        # Clear last_was_tool_use to allow input requests after interrupt
        self.message_processor.last_was_tool_use = False

        # Send confirmation feedback to web UI (this will set last_message_id and last_message_time)
        self._send_feedback_message("Interrupted · What should Claude do instead?")

        # Important: The feedback message above will get a message_id in response.
        # We need to immediately check for any follow-up user messages that might
        # have been queued while we were processing the interrupt.
        # The response from _send_feedback_message already processes queued messages,
        # so we don't need to do anything extra here.

        return True

    def _send_feedback_message(self, message: str) -> None:
        """Send a status update to Vicoa about local control actions."""
        if not self.vicoa_client_sync or not self.agent_instance_id:
            self.log(
                "[WARNING] Cannot send feedback: vicoa_client_sync or agent_instance_id not initialized"
            )
            return

        try:
            response = self.vicoa_client_sync.send_message(
                content=message,
                agent_type=self.agent_name,
                agent_instance_id=self.agent_instance_id,
                requires_user_input=False,
            )

            # Update message tracking so idle detection can work
            if response and hasattr(response, "message_id"):
                import time

                self.message_processor.last_message_id = response.message_id
                self.message_processor.last_message_time = time.time()

            if response and response.queued_user_messages:
                for queued in response.queued_user_messages:
                    # Don't queue control commands - they're handled by control poller
                    # Just check if it's a control command without executing it
                    control_data = self._parse_control_json(queued)
                    if not control_data:
                        self.message_queue.append(queued)

        except Exception as e:
            self.log(f"[ERROR] Failed to send feedback message: {e}")

    async def control_command_poller(self):
        """Async loop to poll for control commands and user messages.

        This allows:
        1. Interrupts and control commands to be processed immediately when Claude is busy
        2. Regular user messages to be sent to the terminal when Claude is busy (Use Case #9)
        3. Messages to be caught even when Claude transitions from busy to idle

        The poller runs continuously to avoid missing messages during state transitions.

        NOTE: This poller does NOT track last_read_message_id because the JSONL monitor
        also fetches messages (via send_agent_message). Instead, we rely on deduplication
        to prevent processing the same message twice.
        """

        while self.running:
            try:
                await asyncio.sleep(1.5)  # Poll every 1.5 seconds

                # Get pending messages without creating a new message
                if not self.vicoa_client_sync or not self.agent_instance_id:
                    continue

                try:
                    # Run sync call in thread pool to avoid blocking async loop
                    loop = asyncio.get_event_loop()

                    # Always pass None to get ALL unread messages
                    # The backend will handle deduplication via instance.last_read_message_id
                    response = await loop.run_in_executor(
                        None,
                        self.vicoa_client_sync.get_pending_messages,
                        self.agent_instance_id,
                        None,  # Always None - get all unread messages
                    )

                    # Process any queued messages (primarily control commands)
                    if response and response.messages:
                        for msg in response.messages:
                            # Track for deduplication
                            self.message_processor.process_user_message_sync(
                                msg.content, from_web=True
                            )

                            # Check if it's a control command
                            is_control = self._handle_control_command(msg.content)

                            if not is_control:
                                # Regular message - queue it for sending when Claude is ready
                                self.message_queue.append(msg.content)

                except Exception as e:
                    # Don't spam logs with connection errors
                    if "Connection" not in str(e) and "Timeout" not in str(e):
                        self.log(f"[WARNING] Control poller error: {e}")
                        import traceback

                        self.log(traceback.format_exc())

            except asyncio.CancelledError:
                break
            except Exception as e:
                self.log(f"[ERROR] Error in control poller: {e}")
