"""Message processing logic for Claude Code Wrapper.

This module handles processing of messages flowing between Claude CLI
and Vicoa servers, including sanitization and state tracking.
"""

import time
from typing import Callable, List, Optional, TYPE_CHECKING

from .deduplicator import MessageDeduplicator

if TYPE_CHECKING:
    from vicoa.sdk.client import VicoaClient
    from integrations.utils.git_utils import GitDiffTracker


class MessageProcessor:
    """Processes messages between Claude CLI and Vicoa servers.

    This class handles:
    - User message processing (from CLI or web)
    - Assistant message processing (from Claude CLI)
    - Message deduplication
    - Idle state tracking
    - Input request state
    """

    def __init__(
        self,
        agent_instance_id: Optional[str],
        agent_name: str,
        vicoa_client: Optional["VicoaClient"],
        git_tracker: Optional["GitDiffTracker"],
        log_func: Callable[[str], None],
    ):
        """Initialize message processor.

        Args:
            agent_instance_id: Agent instance ID for Vicoa
            agent_name: Agent display name
            vicoa_client: Vicoa SDK client (sync)
            git_tracker: Git diff tracker (optional)
            log_func: Logging function
        """
        self.agent_instance_id = agent_instance_id
        self.agent_name = agent_name
        self.vicoa_client = vicoa_client
        self.git_tracker = git_tracker
        self.log = log_func

        # State tracking
        self.last_message_id: Optional[str] = None
        self.last_message_time: Optional[float] = None
        self.pending_input_message_id: Optional[str] = None
        self.last_was_tool_use = False

        # Deduplication
        self.deduplicator = MessageDeduplicator()

        # Requested input tracking (to avoid duplicate requests)
        self.requested_input_messages: set[str] = set()

        # Debouncing for input requests
        self.last_input_request_time: Optional[float] = None
        self.minimum_idle_time: float = 1.0  # seconds before considering "truly idle"
        self.min_request_interval: float = 5.0  # minimum time between input requests

    def process_user_message(
        self,
        content: str,
        from_web: bool,
        input_queue,  # MessageQueue
    ) -> None:
        """Process a user message (sync version for monitor thread).

        Args:
            content: Message content
            from_web: Whether message came from web UI
            input_queue: Message queue for queuing web messages to CLI
        """
        if from_web:
            # Message from web UI - track it to avoid duplicate sends
            self.deduplicator.track(content)
        else:
            # Message from CLI - send to Vicoa if not already from web
            if not self.deduplicator.is_duplicate(
                content
            ) and not self.deduplicator.is_near_duplicate(content):
                if self.agent_instance_id and self.vicoa_client:
                    try:
                        self.vicoa_client.send_user_message(
                            agent_instance_id=self.agent_instance_id,
                            content=content,
                        )
                    except Exception as e:
                        self.log(f"[ERROR] Failed to send CLI message to Vicoa: {e}")
                        import traceback

                        self.log(traceback.format_exc())
                else:
                    self.log(
                        f"[WARNING] Cannot send CLI message: agent_instance_id={self.agent_instance_id}, vicoa_client={self.vicoa_client}"
                    )
            else:
                # Remove from tracking set
                self.deduplicator.remove(content)

            # When user sends a message, we need to:
            # 1. Clear pending_input_message_id to stop any waiting input request
            # 2. Clear last_message_id so we don't request input for old messages
            # NOTE: We do NOT update last_message_time - that only tracks Claude's output
            # This prevents idle detection from using stale timestamps
            self.pending_input_message_id = None
            self.last_message_id = None

    def process_assistant_message(
        self,
        content: str,
        tools_used: List[str],
        send_message_lock,  # threading.Lock
        requested_input_messages: set,
        pending_permission_options: dict,
    ) -> Optional[List[str]]:
        """Process an assistant message (sync version for monitor thread).

        Args:
            content: Message content
            tools_used: List of tools used in this message
            send_message_lock: Lock for thread-safe message sending
            requested_input_messages: Set of messages we've requested input for
            pending_permission_options: Dict of pending permission options

        Returns:
            List of queued user messages, or None
        """
        if not self.agent_instance_id or not self.vicoa_client:
            return None

        # Use lock to ensure atomic message processing
        with send_message_lock:
            # Track if this message uses tools
            self.last_was_tool_use = bool(tools_used)

            # Sanitize content - remove NUL and control characters
            sanitized_content = self._sanitize_content(content)

            # Get git diff if enabled
            git_diff = None
            if self.git_tracker:
                git_diff = self.git_tracker.get_diff()
                if git_diff:
                    git_diff = self._sanitize_content(git_diff)

            # Send to Vicoa
            response = self.vicoa_client.send_message(
                content=sanitized_content,
                agent_type=self.agent_name,
                agent_instance_id=self.agent_instance_id,
                requires_user_input=False,
                git_diff=git_diff,
            )

            # Track message for idle detection
            self.last_message_id = response.message_id
            self.last_message_time = time.time()

            # Clear old tracked input requests since we have a new message
            requested_input_messages.clear()

            # Clear pending permission options since we have a new message
            pending_permission_options.clear()

            # Return queued user messages if any
            if response.queued_user_messages:
                return response.queued_user_messages

            return None

    def should_request_input(
        self, is_claude_idle_func: Callable[[], bool]
    ) -> Optional[str]:
        """Check if we should request input.

        Args:
            is_claude_idle_func: Function that returns True if Claude is idle

        Returns:
            Message ID to request input for, or None
        """
        # FIRST: Check if Claude appears idle (showing "esc to interrupt")
        # This blocks notifications while Claude is actively processing
        is_idle = is_claude_idle_func()
        if not is_idle:
            return None

        # Don't request input if we might have a permission prompt
        # (only applies if Claude is idle, which we've already confirmed above)
        if self.last_was_tool_use:
            # We're in a state where a permission prompt might appear
            return None

        # Basic requirements
        if (
            not self.last_message_id
            or self.last_message_id == self.pending_input_message_id
        ):
            return None

        current_time = time.time()

        # Check if enough time has passed since last message (minimum idle time)
        if self.last_message_time:
            time_since_last_message = current_time - self.last_message_time
            if time_since_last_message < self.minimum_idle_time:
                # Not idle long enough yet
                return None

        # Check if enough time has passed since last input request (prevent rapid requests)
        if self.last_input_request_time:
            time_since_last_request = current_time - self.last_input_request_time
            if time_since_last_request < self.min_request_interval:
                # Too soon since last request
                return None

        # All checks passed - request input
        return self.last_message_id

    def mark_input_requested(self, message_id: str) -> None:
        """Mark that input has been requested for a message.

        Args:
            message_id: Message ID to mark as requested
        """
        self.pending_input_message_id = message_id
        self.last_input_request_time = time.time()

    def _sanitize_content(self, content: str) -> str:
        """Sanitize content - remove NUL and control characters.

        This handles binary content from .docx, PDFs, etc. that might
        break the API.

        Args:
            content: Raw content

        Returns:
            Sanitized content
        """
        return "".join(
            char if ord(char) >= 32 or char in "\n\r\t" else ""
            for char in content.replace("\x00", "")
        )

    def get_last_message_time(self) -> Optional[float]:
        """Get the time of the last message.

        Returns:
            Timestamp of last message, or None
        """
        return self.last_message_time

    def get_last_message_id(self) -> Optional[str]:
        """Get the ID of the last message.

        Returns:
            Last message ID, or None
        """
        return self.last_message_id

    def reset_idle_tracking(self) -> None:
        """Reset idle tracking state."""
        self.last_message_time = time.time()
        self.pending_input_message_id = None

    def process_user_message_sync(self, content: str, from_web: bool = False) -> None:
        """Process a user message for deduplication tracking.

        This doesn't send the message, just tracks it for deduplication.

        Args:
            content: Message content
            from_web: Whether this message came from the web UI
        """
        # Track for deduplication
        self.deduplicator.process_user_message(content, from_web=from_web)
