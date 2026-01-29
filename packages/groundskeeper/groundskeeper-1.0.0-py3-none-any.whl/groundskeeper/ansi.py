"""ANSI escape sequence parsing and conversion utilities.

Converts ANSI-styled text to Rich Text objects for display in Textual widgets.
"""

import re

from rich.text import Text


def ansi_to_rich(text: str) -> Text:
    """Convert ANSI escape sequences to Rich Text object.

    Uses Rich's built-in ANSI parsing for accurate conversion of:
    - Standard colors (30-37 fg, 40-47 bg, 90-97 bright fg, 100-107 bright bg)
    - 256 color palette (38;5;N, 48;5;N)
    - RGB colors (38;2;R;G;B, 48;2;R;G;B)
    - Text styles (bold, dim, italic, underline, reverse, strikethrough)
    - Reset codes

    Args:
        text: String potentially containing ANSI escape sequences

    Returns:
        Rich Text object with appropriate styling applied

    Examples:
        >>> ansi_to_rich("\x1b[31mRed text\x1b[0m")
        Text('Red text', style='red')

        >>> ansi_to_rich("Plain text")
        Text('Plain text')
    """
    if not text:
        return Text()

    # Rich's Text.from_ansi handles all ANSI codes natively
    return Text.from_ansi(text)


def contains_ansi(text: str) -> bool:
    """Check if text contains ANSI escape sequences.

    Detects the presence of ANSI escape codes by looking for the
    standard escape sequence pattern: ESC [ (CSI - Control Sequence Introducer)

    Args:
        text: String to check for ANSI sequences

    Returns:
        True if ANSI escape sequences are present, False otherwise

    Examples:
        >>> contains_ansi("\x1b[31mRed\x1b[0m")
        True

        >>> contains_ansi("Plain text")
        False
    """
    if not text:
        return False

    # Check for ESC [ pattern (CSI - Control Sequence Introducer)
    return "\x1b[" in text


def strip_ansi(text: str) -> str:
    """Remove all ANSI escape sequences from text.

    Strips ANSI codes to return plain text without styling.
    Handles:
    - CSI sequences: ESC [ ... m (colors, styles)
    - OSC sequences: ESC ] ... (operating system commands)
    - Other escape sequences

    Args:
        text: String potentially containing ANSI escape sequences

    Returns:
        Plain text with all ANSI codes removed

    Examples:
        >>> strip_ansi("\x1b[31mRed text\x1b[0m")
        'Red text'

        >>> strip_ansi("Plain text")
        'Plain text'

        >>> strip_ansi("\x1b[1;32mBold green\x1b[0m normal")
        'Bold green normal'
    """
    if not text:
        return text

    # Pattern matches:
    # - ESC [ ... (any char from @ to ~) - CSI sequences
    # - ESC ] ... (BEL or ESC \) - OSC sequences
    # - ESC (any single char) - other escape sequences
    ansi_pattern = re.compile(
        r"\x1b"  # ESC
        r"(?:"
        r"\[[0-9;]*[a-zA-Z@-~]"  # CSI: ESC [ params letter
        r"|\][^\x07\x1b]*(?:\x07|\x1b\\)"  # OSC: ESC ] ... BEL/ESC\
        r"|[^\[]"  # Other: ESC + single char
        r")"
    )

    return ansi_pattern.sub("", text)
