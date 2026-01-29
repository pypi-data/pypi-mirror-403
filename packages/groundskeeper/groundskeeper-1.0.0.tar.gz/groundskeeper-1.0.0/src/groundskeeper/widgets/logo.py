"""Groundskeeper-inspired ASCII art logo widget."""

from textual.reactive import reactive
from textual.widgets import Static

# Full ASCII art logo - Groundskeeper's distinctive silhouette
GROUNDSKEEPER_LOGO_FULL = """\
[bold $warning]     .---.
    /     \\
   | o   o |
    \\  ^  /[/]  [bold $primary]GROUNDSKEEPER[/]
[bold $warning]     |___|[/]   [dim]════════════════[/]
[bold $warning]    /|   |\\[/]  [italic $text-muted]"Back to work!"[/]
[bold $warning]   (_|   |_)[/]
"""

# Compact single-line logo with Groundskeeper's iconic pose
GROUNDSKEEPER_LOGO_COMPACT = "[bold $warning]ᕦ(ò_óˇ)ᕤ[/] [bold $primary]groundskeeper[/]"


class Logo(Static):
    """Groundskeeper-inspired ASCII logo with adaptive sizing.

    In compact mode (default), shows a single-line logo with Groundskeeper emoji.
    In expanded mode, shows full ASCII art.
    """

    DEFAULT_CSS = """
    Logo {
        width: auto;
        height: auto;
    }

    Logo.expanded {
        height: 7;
        padding: 0;
    }
    """

    compact = reactive(True)

    def __init__(
        self,
        compact: bool = True,
        *,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
    ) -> None:
        super().__init__(name=name, id=id, classes=classes)
        self.compact = compact

    def render(self) -> str:
        return GROUNDSKEEPER_LOGO_COMPACT if self.compact else GROUNDSKEEPER_LOGO_FULL

    def watch_compact(self, compact: bool) -> None:
        if compact:
            self.remove_class("expanded")
        else:
            self.add_class("expanded")
        self.refresh()

    def toggle(self) -> None:
        """Toggle between compact and expanded modes."""
        self.compact = not self.compact
