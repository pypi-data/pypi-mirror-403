"""Claude CLI binary discovery utilities.

This module provides utilities for finding the Claude CLI executable
in various standard installation locations.
"""

import shutil
from pathlib import Path


def find_claude_cli() -> str:
    """Find Claude CLI binary.

    Searches in the following locations:
    1. System PATH (via shutil.which)
    2. ~/.npm-global/bin/claude
    3. /usr/local/bin/claude
    4. ~/.local/bin/claude
    5. ~/node_modules/.bin/claude
    6. ~/.yarn/bin/claude
    7. ~/.claude/local/claude

    Returns:
        Path to Claude CLI binary

    Raises:
        FileNotFoundError: If Claude CLI is not found
    """
    # Check if it's in PATH
    if cli := shutil.which("claude"):
        return cli

    # Check common installation locations
    locations = [
        Path.home() / ".npm-global/bin/claude",
        Path("/usr/local/bin/claude"),
        Path.home() / ".local/bin/claude",
        Path.home() / "node_modules/.bin/claude",
        Path.home() / ".yarn/bin/claude",
        Path.home() / ".claude/local/claude",
    ]

    for path in locations:
        if path.exists() and path.is_file():
            return str(path)

    raise FileNotFoundError(
        "Claude CLI not found. Install with: npm install -g @anthropic-ai/claude-code"
    )
