"""AskUserQuestion detector for Claude CLI.

This detector identifies when Claude uses the AskUserQuestion tool
and extracts the question text and available options.
"""

import re
from typing import Dict, List, Optional

from .base import BaseDetector, DetectionResult


class QuestionDetector(BaseDetector):
    """Detects AskUserQuestion prompts in terminal output.

    AskUserQuestion is a tool Claude uses to present multiple-choice questions.
    The UI shows:
    - A question text
    - Numbered options (1-5)
    - Optional descriptions for each option
    - "Enter to select" and "Tab/Arrow keys to navigate" hints
    """

    # Markers that indicate AskUserQuestion
    SELECT_MARKER = "Enter to select"
    NAVIGATE_MARKER = "Tab/Arrow keys to navigate"

    # Pattern to match option lines (1. through 5.)
    OPTION_PATTERN = re.compile(r"^[1-5]\.\s+(.+)")

    # UI elements to skip when searching for question
    SKIP_PATTERNS = [
        "Enter to select",
        "Tab/Arrow keys",
        "Esc to cancel",
        "Submit",
        "for shortcuts",
        "thinking off",
        "thinking on",
        "Try ",
    ]

    # UI element regex patterns
    UI_ELEMENT_PATTERN = re.compile(r"^[←☐✔→\s]+$")
    UI_HEADER_PATTERN = re.compile(r"^[←☐✔→].*[←☐✔→]$")

    # Unicode characters to clean
    BORDER_CHAR = "\u2502"  # │
    ARROW_CHAR = "\u276f"  # ❯
    SELECTION_MARKER = "❯"

    def detect(self, clean_buffer: str) -> bool:
        """Check if AskUserQuestion prompt is present in the buffer.

        Args:
            clean_buffer: Terminal buffer with ANSI codes removed

        Returns:
            True if AskUserQuestion detected, False otherwise
        """
        return (
            self.SELECT_MARKER in clean_buffer and self.NAVIGATE_MARKER in clean_buffer
        )

    def extract(self, clean_buffer: str) -> DetectionResult:
        """Extract question and options from the buffer.

        Args:
            clean_buffer: Terminal buffer with ANSI codes removed

        Returns:
            DetectionResult with question data, or not_detected
        """
        if not self.detect(clean_buffer):
            return DetectionResult.not_detected()

        # Extract question text
        question = self._extract_question(clean_buffer)

        # Extract options
        options_dict = self._extract_options(clean_buffer)

        # Validate extraction
        if not question or len(question) < 10 or "?" not in question:
            # Invalid question
            question = "Waiting for your input..."
            options_list = []
            options_dict = {}
        elif not options_dict or len(options_dict) < 2:
            # Invalid options
            options_list = []
            options_dict = {}
        else:
            options_list = list(options_dict.values())

        data = {
            "question": question,
            "options": options_list,
            "options_map": options_dict,
            "type": "ask_user_question",
        }

        return DetectionResult.success(data)

    def _extract_question(self, clean_buffer: str) -> str:
        """Extract the question text from the buffer.

        The question is typically located between the beginning of the prompt
        and the first numbered option.

        Args:
            clean_buffer: Terminal buffer with ANSI codes removed

        Returns:
            Extracted question text, or empty string if not found
        """
        lines = clean_buffer.split("\n")

        # Find the last occurrence of "Enter to select" - this marks the current prompt
        enter_to_select_idx = self._find_last_marker(lines, self.SELECT_MARKER)

        if enter_to_select_idx is None:
            return ""

        # Find the LAST occurrence of "1." before "Enter to select"
        first_option_idx = self._find_first_option(lines, enter_to_select_idx)

        if first_option_idx is None:
            return ""

        # Look for question between reasonable point and first option
        search_start = max(0, first_option_idx - 20)

        # Search backwards from first option to find the question
        for i in range(first_option_idx - 1, search_start - 1, -1):
            line = lines[i]
            cleaned = self._clean_question_line(line)

            if self._is_valid_question_line(cleaned):
                return cleaned

        return ""

    def _extract_options(self, clean_buffer: str) -> Dict[str, str]:
        """Extract numbered options from the buffer.

        Args:
            clean_buffer: Terminal buffer with ANSI codes removed

        Returns:
            Dictionary mapping option numbers to option text
        """
        lines = clean_buffer.split("\n")

        # Find the last occurrence of "Enter to select"
        enter_to_select_idx = self._find_last_marker(lines, self.SELECT_MARKER)

        if enter_to_select_idx is None:
            return {}

        # Find all option lines (1-5) between reasonable range and "Enter to select"
        search_start = max(0, enter_to_select_idx - 30)
        option_starts = []

        for i in range(search_start, enter_to_select_idx):
            clean_line = self._clean_option_line(lines[i])
            if self.OPTION_PATTERN.match(clean_line):
                option_starts.append(i)

        if not option_starts:
            return {}

        # Extract consecutive numbered options from the first found option
        return self._parse_options_from_start(lines, option_starts[0])

    def _parse_options_from_start(
        self, lines: List[str], start_line: int
    ) -> Dict[str, str]:
        """Parse options starting from a specific line.

        Args:
            lines: List of buffer lines
            start_line: Line index to start parsing from

        Returns:
            Dictionary mapping option numbers to option text
        """
        options_dict = {}
        current_num = 1
        current_option_key = None

        for i in range(start_line, min(start_line + 20, len(lines))):
            raw_line = lines[i]
            clean_line = self._clean_option_line(raw_line)

            # Check if this is a numbered option
            pattern = rf"^{current_num}\.\s+(.+)"
            match = re.match(pattern, clean_line)

            if match:
                # Found option N
                current_option_key = str(current_num)
                options_dict[current_option_key] = clean_line
                current_num += 1

            elif current_option_key and clean_line and current_num <= 6:
                # Check if we hit navigation hints (stop parsing)
                if any(
                    marker in clean_line
                    for marker in [self.SELECT_MARKER, self.NAVIGATE_MARKER]
                ):
                    break

                # Check if this is a description line (indented continuation)
                raw_without_border = raw_line.replace(self.BORDER_CHAR, " ")
                raw_without_border = raw_without_border.replace(
                    self.SELECTION_MARKER, " "
                )

                if raw_without_border.startswith((" ", "\t")) and not re.match(
                    r"^[1-5]\.\s+", clean_line
                ):
                    # Append description to current option
                    existing = options_dict[current_option_key].rstrip()
                    options_dict[current_option_key] = (
                        f"{existing} - {clean_line}".strip()
                    )

            elif any(
                marker in clean_line
                for marker in [self.SELECT_MARKER, self.NAVIGATE_MARKER]
            ):
                # Stop when we hit navigation hints
                break

        return options_dict

    def _find_last_marker(self, lines: List[str], marker: str) -> Optional[int]:
        """Find the last occurrence of a marker in the lines.

        Args:
            lines: List of lines to search
            marker: Marker text to find

        Returns:
            Index of last occurrence, or None if not found
        """
        for i in range(len(lines) - 1, -1, -1):
            if marker in lines[i]:
                return i
        return None

    def _find_first_option(self, lines: List[str], before_idx: int) -> Optional[int]:
        """Find the first option line before a given index.

        Args:
            lines: List of lines to search
            before_idx: Search before this index

        Returns:
            Index of first option, or None if not found
        """
        for i in range(before_idx - 1, max(0, before_idx - 50), -1):
            line_check = lines[i].strip().replace(self.SELECTION_MARKER, "").strip()
            line_check = line_check.replace(self.BORDER_CHAR, "").strip()

            if re.match(r"^\s*1\.\s+\w", line_check):
                return i

        return None

    def _clean_question_line(self, line: str) -> str:
        """Clean a line that might contain a question.

        Args:
            line: Raw line from buffer

        Returns:
            Cleaned line
        """
        cleaned = line.strip()
        cleaned = cleaned.replace(self.BORDER_CHAR, "")
        cleaned = cleaned.replace(self.ARROW_CHAR, "")
        cleaned = cleaned.replace(self.SELECTION_MARKER, "")
        return cleaned.strip()

    def _clean_option_line(self, line: str) -> str:
        """Clean a line that might contain an option.

        Args:
            line: Raw line from buffer

        Returns:
            Cleaned line
        """
        cleaned = line.strip()
        cleaned = cleaned.replace(self.BORDER_CHAR, "").strip()
        cleaned = cleaned.replace(self.ARROW_CHAR, "").strip()
        cleaned = cleaned.replace(self.SELECTION_MARKER, "").strip()
        return cleaned

    def _is_valid_question_line(self, line: str) -> bool:
        """Check if a line is a valid question line.

        Args:
            line: Cleaned line to check

        Returns:
            True if valid question line, False otherwise
        """
        if not line or len(line) <= 10:
            return False

        # Skip lines starting with option numbers
        if line.startswith(("1.", "2.", "3.", "4.", "5.", ">", ">>")):
            return False

        # Skip navigation hints and UI elements
        if any(pattern in line for pattern in self.SKIP_PATTERNS):
            return False

        # Skip pure UI elements
        if self.UI_ELEMENT_PATTERN.match(line) or self.UI_HEADER_PATTERN.match(line):
            return False

        # Questions should contain a question mark
        if "?" not in line:
            return False

        # Check that line contains mostly printable characters
        printable_chars = sum(1 for c in line if c.isprintable())
        if printable_chars < len(line) * 0.7:
            return False

        return True

    def get_patterns(self) -> Dict[str, str]:
        """Get the patterns used by this detector.

        Returns:
            Dictionary of pattern names to pattern strings
        """
        return {
            "select_marker": self.SELECT_MARKER,
            "navigate_marker": self.NAVIGATE_MARKER,
            "option_pattern": self.OPTION_PATTERN.pattern,
        }
