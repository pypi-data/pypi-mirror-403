"""Permission prompt detector for Claude CLI.

This detector identifies standard permission prompts when Claude
requests permission to perform actions (e.g., file operations).
"""

import re
from typing import Dict, List, Optional

from .base import BaseDetector, DetectionResult


class PermissionDetector(BaseDetector):
    """Detects permission prompts in terminal output.

    Permission prompts typically show:
    - A question starting with "Do you want..." or "What do you want to do..."
    - Numbered options (typically 3):
      1. Yes
      2. Yes, and don't ask again this session
      3. No
    - "(esc to cancel)" or "(escape to cancel)" hint
    """

    # Primary keywords that indicate a permission prompt
    # Expanded to cover more prompt variations (e.g., "Would you like to proceed?")
    PRIMARY_KEYWORDS = [
        "Do you want",
        "Would you like",
        "What do you want to do",
    ]

    def __init__(self):
        """Initialize permission detector."""
        super().__init__()
        self._question_line_idx = 0

    # Escape hint that's typically present
    ESC_HINT = "(esc"
    ESC_CANCEL = "esc to cancel"
    ESCAPE_CANCEL = "escape to cancel"

    # Pattern to match numbered options with optional non-digit prefix
    OPTION_PATTERN = re.compile(r"^[^\d]*(\d+)[\.)]\s+(.+)")

    # Default options if extraction fails
    DEFAULT_OPTIONS = {
        "1": "1. Yes",
        "2": "2. Yes, and don't ask again this session",
        "3": "3. No",
    }

    # Unicode characters to clean
    BORDER_CHAR = "\u2502"  # │

    # Separator line detection (box drawing / dash heavy)
    SEPARATOR_PATTERN = re.compile(
        r"^[\s\-\u2500\u2501\u2504\u2505\u2508\u2509\u250c\u2510\u2514\u2518\u251c\u2524\u252c\u2534\u253c]+$"
    )

    # Selection markers that can prefix the focused option
    SELECTION_MARKER_PATTERN = re.compile(
        r"^[\s\u200b\u200e\u200f\u2060]*(?:[❯>▶▸›»]+)\s*"
    )

    def detect(self, clean_buffer: str) -> bool:
        """Check if a permission prompt is present in the buffer.

        Args:
            clean_buffer: Terminal buffer with ANSI codes removed

        Returns:
            True if permission prompt detected, False otherwise
        """
        # Permission prompt is detected by:
        # 1. Presence of a permission question keyword
        # 2. Presence of escape hint
        has_question = any(kw in clean_buffer for kw in self.PRIMARY_KEYWORDS)
        return has_question and self._has_numbered_options(clean_buffer)

    def extract(self, clean_buffer: str) -> DetectionResult:
        """Extract question and options from the buffer.

        Args:
            clean_buffer: Terminal buffer with ANSI codes removed

        Returns:
            DetectionResult with permission data, or not_detected
        """
        if not self.detect(clean_buffer):
            return DetectionResult.not_detected()

        # Reset question line index for fresh extraction
        self._question_line_idx = 0

        # Extract question
        question = self._extract_question(clean_buffer)

        # Extract options
        options_dict = self._extract_options(clean_buffer)

        # Validate extraction
        if not question:
            question = "Permission required"

        if not options_dict or len(options_dict) < 2:
            return DetectionResult.not_detected()

        options_list = list(options_dict.values())

        # Build options mapping (option text -> number)
        options_map = {}
        for option_num, option_text in options_dict.items():
            clean_text = option_text.strip()
            options_map[clean_text] = option_num
            if ". " in clean_text:
                _, stripped = clean_text.split(". ", 1)
                stripped = stripped.strip()
                if stripped:
                    options_map[stripped] = option_num

        data = {
            "question": question,
            "options": options_list,
            "options_map": options_map,
            "type": "permission",
        }

        return DetectionResult.success(data)

    def _extract_question(self, clean_buffer: str) -> str:
        """Extract the question text from the buffer.

        Args:
            clean_buffer: Terminal buffer with ANSI codes removed

        Returns:
            Extracted question text, or empty string if not found
        """
        normalized_buffer = clean_buffer.replace("\r", "\n")
        lines = normalized_buffer.split("\n")

        # Look for "Do you want" line - search from end to get most recent
        for i in range(len(lines) - 1, -1, -1):
            raw_line = lines[i]
            line_clean = raw_line.strip().replace(self.BORDER_CHAR, "").strip()
            if self._is_separator_line(line_clean):
                continue

            if any(kw in line_clean for kw in self.PRIMARY_KEYWORDS):
                # Store the line index for use in _extract_options
                self._question_line_idx = i
                return self._extract_question_text(line_clean)

        return ""

    def _extract_options(self, clean_buffer: str) -> Dict[str, str]:
        """Extract numbered options from the buffer.

        Args:
            clean_buffer: Terminal buffer with ANSI codes removed

        Returns:
            Dictionary mapping option numbers to option text
        """
        normalized_buffer = clean_buffer.replace("\r", "\n")
        lines = normalized_buffer.split("\n")
        options_dict = {}

        # Only scan lines AFTER the question line to avoid picking up old numbered lists
        start_idx = getattr(self, "_question_line_idx", 0)

        # Look ahead up to 15 lines after the question (permission prompts are compact)
        end_idx = min(len(lines), start_idx + 15)

        # Find lines that look like numbered options within the relevant region
        for i in range(start_idx, end_idx):
            line = lines[i]
            # Clean the line
            cleaned = line.strip().replace(self.BORDER_CHAR, "").strip()
            cleaned = self._strip_selection_marker(cleaned)
            if self._is_separator_line(cleaned):
                continue

            # Try to match numbered option pattern
            match = self.OPTION_PATTERN.match(cleaned)
            if match:
                option_num = match.group(1)
                option_text = match.group(2).strip()

                # Skip if this looks like metadata (e.g., "1. 2024-01-19")
                if option_text and not option_text[0].isdigit():
                    options_dict[option_num] = f"{option_num}. {option_text}"

        return options_dict

    def _extract_question_text(self, line: str) -> str:
        """Extract the question sentence from a noisy line."""
        for keyword in self.PRIMARY_KEYWORDS:
            if keyword in line:
                start_idx = line.find(keyword)
                if start_idx == -1:
                    continue
                candidate = line[start_idx:].strip()
                question_match = re.search(r"^.*?\?", candidate)
                return question_match.group(0).strip() if question_match else candidate
        return line.strip()

    def _is_separator_line(self, line: str) -> bool:
        """Return True if the line is just a separator."""
        if not line:
            return True
        if self.SEPARATOR_PATTERN.match(line):
            return True
        alnum_count = sum(1 for c in line if c.isalnum())
        return alnum_count == 0 and len(line) > 10

    def _strip_selection_marker(self, line: str) -> str:
        """Strip known selection markers from the start of an option line."""
        cleaned = self.SELECTION_MARKER_PATTERN.sub("", line)
        return cleaned.strip()

    def _has_numbered_options(self, clean_buffer: str) -> bool:
        """Check if the buffer contains at least two numbered options."""
        normalized_buffer = clean_buffer.replace("\r", "\n")
        lines = normalized_buffer.split("\n")
        count = 0
        for line in lines:
            cleaned = line.strip().replace(self.BORDER_CHAR, "").strip()
            cleaned = self._strip_selection_marker(cleaned)
            if self._is_separator_line(cleaned):
                continue
            if self.OPTION_PATTERN.match(cleaned):
                count += 1
                if count >= 2:
                    return True
        return False

    def _find_question_line_index(self, lines: List[str]) -> Optional[int]:
        """Find the index of the line containing the question.

        Args:
            lines: List of buffer lines

        Returns:
            Index of question line, or None if not found
        """
        for i in range(len(lines) - 1, -1, -1):
            line_clean = lines[i].strip().replace(self.BORDER_CHAR, "").strip()
            if any(kw in line_clean for kw in self.PRIMARY_KEYWORDS):
                return i
        return None

    def _find_options_region(
        self, lines: List[str], question_idx: int
    ) -> Optional[tuple[int, int]]:
        """Find the region containing option lines.

        Args:
            lines: List of buffer lines
            question_idx: Index of the question line

        Returns:
            Tuple of (start_idx, end_idx) for options region, or None
        """
        # Look for options after the question (up to 10 lines)
        start_idx = question_idx + 1
        end_idx = min(len(lines), question_idx + 11)

        # Verify we have at least one option in this region
        for i in range(start_idx, end_idx):
            cleaned = lines[i].strip().replace(self.BORDER_CHAR, "").strip()
            if self.OPTION_PATTERN.match(cleaned):
                return (start_idx, end_idx)

        return None

    def get_patterns(self) -> Dict[str, str]:
        """Get the patterns used by this detector.

        Returns:
            Dictionary of pattern names to pattern strings
        """
        return {
            "primary_keywords": str(self.PRIMARY_KEYWORDS),
            "esc_hint": self.ESC_HINT,
            "esc_cancel": self.ESC_CANCEL,
            "escape_cancel": self.ESCAPE_CANCEL,
            "option_pattern": self.OPTION_PATTERN.pattern,
        }
