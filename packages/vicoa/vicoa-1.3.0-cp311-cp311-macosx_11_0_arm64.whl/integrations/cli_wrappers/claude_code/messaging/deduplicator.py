"""Message deduplication utilities.

This module provides functionality to track and deduplicate messages
to avoid sending the same message multiple times.
"""

import time
from collections import deque
from typing import Deque, Set, Tuple


class MessageDeduplicator:
    """Tracks messages to prevent duplicate sends.

    This is particularly important for messages coming from the web UI
    that we don't want to echo back to the server.
    """

    def __init__(self):
        """Initialize the deduplicator."""
        self._tracked_messages: Set[str] = set()
        self._recent_messages: Deque[Tuple[float, str]] = deque()
        self._recent_window_seconds = 10.0

    def track(self, content: str) -> None:
        """Track a message to mark it as seen.

        Args:
            content: Message content to track
        """
        self._tracked_messages.add(content)
        normalized = self._normalize(content)
        if normalized:
            self._recent_messages.append((time.time(), normalized))
            self._trim_recent()

    def is_duplicate(self, content: str) -> bool:
        """Check if a message has been seen before.

        Args:
            content: Message content to check

        Returns:
            True if message has been seen, False otherwise
        """
        return content in self._tracked_messages

    def is_near_duplicate(self, content: str) -> bool:
        """Check if a message is a near-duplicate of a recent tracked message."""
        normalized = self._normalize(content)
        if not normalized:
            return False

        self._trim_recent()
        for _, recent in self._recent_messages:
            if normalized == recent:
                return True
            if len(recent) >= len(normalized) + 5 and (
                recent.startswith(normalized) or recent.endswith(normalized)
            ):
                return True
            if len(normalized) >= len(recent) + 5 and (
                normalized.startswith(recent) or normalized.endswith(recent)
            ):
                return True
        return False

    def remove(self, content: str) -> None:
        """Remove a message from tracking.

        This is useful after processing a message to allow
        the same content to be sent again if needed.

        Args:
            content: Message content to remove from tracking
        """
        self._tracked_messages.discard(content)

    def clear(self) -> None:
        """Clear all tracked messages."""
        self._tracked_messages.clear()

    def process_user_message(self, content: str, from_web: bool = False) -> None:
        """Process a user message for deduplication.

        Args:
            content: Message content
            from_web: Whether message came from web UI
        """
        # Track all user messages for deduplication
        self.track(content)

    def size(self) -> int:
        """Get the number of tracked messages.

        Returns:
            Number of tracked messages
        """
        return len(self._tracked_messages)

    def __len__(self) -> int:
        """Get the number of tracked messages (same as size()).

        Returns:
            Number of tracked messages
        """
        return len(self._tracked_messages)

    def __contains__(self, content: str) -> bool:
        """Check if content is tracked (allows 'in' operator).

        Args:
            content: Message content to check

        Returns:
            True if tracked, False otherwise
        """
        return content in self._tracked_messages

    def _normalize(self, content: str) -> str:
        """Normalize content for fuzzy deduplication."""
        return " ".join(content.split()).strip()

    def _trim_recent(self) -> None:
        """Trim old recent messages outside the deduplication window."""
        cutoff = time.time() - self._recent_window_seconds
        while self._recent_messages and self._recent_messages[0][0] < cutoff:
            self._recent_messages.popleft()
