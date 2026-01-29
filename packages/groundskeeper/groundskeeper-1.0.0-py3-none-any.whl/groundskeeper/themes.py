"""Terminal theme definitions for Groundskeeper TUI.

This module provides a collection of popular terminal color schemes using
rich.terminal_theme.TerminalTheme for use in the Textual application.
"""

from rich.terminal_theme import TerminalTheme


def hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    """Convert hex color string to RGB tuple.

    Args:
        hex_color: Hex color string (e.g., "#FF5555" or "FF5555")

    Returns:
        Tuple of (red, green, blue) values (0-255)
    """
    hex_color = hex_color.lstrip("#")
    r = int(hex_color[0:2], 16)
    g = int(hex_color[2:4], 16)
    b = int(hex_color[4:6], 16)
    return (r, g, b)


# Dracula theme - https://draculatheme.com/
DRACULA = TerminalTheme(
    background=hex_to_rgb("#282A36"),
    foreground=hex_to_rgb("#F8F8F2"),
    normal=[
        hex_to_rgb("#21222C"),  # black
        hex_to_rgb("#FF5555"),  # red
        hex_to_rgb("#50FA7B"),  # green
        hex_to_rgb("#F1FA8C"),  # yellow
        hex_to_rgb("#BD93F9"),  # blue
        hex_to_rgb("#FF79C6"),  # magenta
        hex_to_rgb("#8BE9FD"),  # cyan
        hex_to_rgb("#F8F8F2"),  # white
    ],
    bright=[
        hex_to_rgb("#6272A4"),  # bright black
        hex_to_rgb("#FF6E6E"),  # bright red
        hex_to_rgb("#69FF94"),  # bright green
        hex_to_rgb("#FFFFA5"),  # bright yellow
        hex_to_rgb("#D6ACFF"),  # bright blue
        hex_to_rgb("#FF92DF"),  # bright magenta
        hex_to_rgb("#A4FFFF"),  # bright cyan
        hex_to_rgb("#FFFFFF"),  # bright white
    ],
)

# Nord theme - https://www.nordtheme.com/
NORD = TerminalTheme(
    background=hex_to_rgb("#2E3440"),  # nord0
    foreground=hex_to_rgb("#D8DEE9"),  # nord4
    normal=[
        hex_to_rgb("#3B4252"),  # black (nord1)
        hex_to_rgb("#BF616A"),  # red (nord11)
        hex_to_rgb("#A3BE8C"),  # green (nord14)
        hex_to_rgb("#EBCB8B"),  # yellow (nord13)
        hex_to_rgb("#81A1C1"),  # blue (nord9)
        hex_to_rgb("#B48EAD"),  # magenta (nord15)
        hex_to_rgb("#88C0D0"),  # cyan (nord8)
        hex_to_rgb("#E5E9F0"),  # white (nord5)
    ],
    bright=[
        hex_to_rgb("#4C566A"),  # bright black (nord3)
        hex_to_rgb("#BF616A"),  # bright red (same as normal)
        hex_to_rgb("#A3BE8C"),  # bright green (same as normal)
        hex_to_rgb("#EBCB8B"),  # bright yellow (same as normal)
        hex_to_rgb("#81A1C1"),  # bright blue (same as normal)
        hex_to_rgb("#B48EAD"),  # bright magenta (same as normal)
        hex_to_rgb("#88C0D0"),  # bright cyan (same as normal)
        hex_to_rgb("#ECEFF4"),  # bright white (nord6)
    ],
)

# Gruvbox Dark theme - https://github.com/morhetz/gruvbox
GRUVBOX_DARK = TerminalTheme(
    background=hex_to_rgb("#282828"),
    foreground=hex_to_rgb("#EBDBB2"),
    normal=[
        hex_to_rgb("#282828"),  # black
        hex_to_rgb("#CC241D"),  # red
        hex_to_rgb("#98971A"),  # green
        hex_to_rgb("#D79921"),  # yellow
        hex_to_rgb("#458588"),  # blue
        hex_to_rgb("#B16286"),  # magenta
        hex_to_rgb("#689D6A"),  # cyan
        hex_to_rgb("#A89984"),  # white
    ],
    bright=[
        hex_to_rgb("#928374"),  # bright black
        hex_to_rgb("#FB4934"),  # bright red
        hex_to_rgb("#B8BB26"),  # bright green
        hex_to_rgb("#FABD2F"),  # bright yellow
        hex_to_rgb("#83A598"),  # bright blue
        hex_to_rgb("#D3869B"),  # bright magenta
        hex_to_rgb("#8EC07C"),  # bright cyan
        hex_to_rgb("#EBDBB2"),  # bright white
    ],
)

# Tokyo Night theme - https://github.com/folke/tokyonight.nvim
TOKYO_NIGHT = TerminalTheme(
    background=hex_to_rgb("#1A1B26"),
    foreground=hex_to_rgb("#C0CAF5"),
    normal=[
        hex_to_rgb("#15161E"),  # black
        hex_to_rgb("#F7768E"),  # red
        hex_to_rgb("#9ECE6A"),  # green
        hex_to_rgb("#E0AF68"),  # yellow
        hex_to_rgb("#7AA2F7"),  # blue
        hex_to_rgb("#BB9AF7"),  # magenta
        hex_to_rgb("#7DCFFF"),  # cyan
        hex_to_rgb("#A9B1D6"),  # white
    ],
    bright=[
        hex_to_rgb("#414868"),  # bright black
        hex_to_rgb("#F7768E"),  # bright red (same as normal)
        hex_to_rgb("#9ECE6A"),  # bright green (same as normal)
        hex_to_rgb("#E0AF68"),  # bright yellow (same as normal)
        hex_to_rgb("#7AA2F7"),  # bright blue (same as normal)
        hex_to_rgb("#BB9AF7"),  # bright magenta (same as normal)
        hex_to_rgb("#7DCFFF"),  # bright cyan (same as normal)
        hex_to_rgb("#C0CAF5"),  # bright white
    ],
)

# Catppuccin Mocha theme - https://github.com/catppuccin/catppuccin
CATPPUCCIN_MOCHA = TerminalTheme(
    background=hex_to_rgb("#1E1E2E"),  # base
    foreground=hex_to_rgb("#CDD6F4"),  # text
    normal=[
        hex_to_rgb("#45475A"),  # black (surface1)
        hex_to_rgb("#F38BA8"),  # red
        hex_to_rgb("#A6E3A1"),  # green
        hex_to_rgb("#F9E2AF"),  # yellow
        hex_to_rgb("#89B4FA"),  # blue
        hex_to_rgb("#F5C2E7"),  # magenta (pink)
        hex_to_rgb("#94E2D5"),  # cyan (teal)
        hex_to_rgb("#BAC2DE"),  # white (subtext1)
    ],
    bright=[
        hex_to_rgb("#585B70"),  # bright black (surface2)
        hex_to_rgb("#F38BA8"),  # bright red (same as normal)
        hex_to_rgb("#A6E3A1"),  # bright green (same as normal)
        hex_to_rgb("#F9E2AF"),  # bright yellow (same as normal)
        hex_to_rgb("#89B4FA"),  # bright blue (same as normal)
        hex_to_rgb("#F5C2E7"),  # bright magenta (same as normal)
        hex_to_rgb("#94E2D5"),  # bright cyan (same as normal)
        hex_to_rgb("#A6ADC8"),  # bright white (subtext0)
    ],
)

# Solarized Dark theme - https://ethanschoonover.com/solarized/
SOLARIZED_DARK = TerminalTheme(
    background=hex_to_rgb("#002B36"),
    foreground=hex_to_rgb("#839496"),
    normal=[
        hex_to_rgb("#073642"),  # black
        hex_to_rgb("#DC322F"),  # red
        hex_to_rgb("#859900"),  # green
        hex_to_rgb("#B58900"),  # yellow
        hex_to_rgb("#268BD2"),  # blue
        hex_to_rgb("#D33682"),  # magenta
        hex_to_rgb("#2AA198"),  # cyan
        hex_to_rgb("#EEE8D5"),  # white
    ],
    bright=[
        hex_to_rgb("#002B36"),  # bright black (same as background)
        hex_to_rgb("#DC322F"),  # bright red (same as normal)
        hex_to_rgb("#859900"),  # bright green (same as normal)
        hex_to_rgb("#B58900"),  # bright yellow (same as normal)
        hex_to_rgb("#268BD2"),  # bright blue (same as normal)
        hex_to_rgb("#D33682"),  # bright magenta (same as normal)
        hex_to_rgb("#2AA198"),  # bright cyan (same as normal)
        hex_to_rgb("#FDF6E3"),  # bright white
    ],
)


# Theme registry
THEMES: dict[str, TerminalTheme] = {
    "dracula": DRACULA,
    "nord": NORD,
    "gruvbox-dark": GRUVBOX_DARK,
    "tokyo-night": TOKYO_NIGHT,
    "catppuccin-mocha": CATPPUCCIN_MOCHA,
    "solarized-dark": SOLARIZED_DARK,
}

# Default theme
DEFAULT_THEME = "dracula"


def get_theme(name: str) -> TerminalTheme | None:
    """Get a terminal theme by name.

    Args:
        name: Theme name (e.g., "dracula", "nord", "gruvbox-dark")

    Returns:
        TerminalTheme instance if found, None otherwise
    """
    return THEMES.get(name.lower())
