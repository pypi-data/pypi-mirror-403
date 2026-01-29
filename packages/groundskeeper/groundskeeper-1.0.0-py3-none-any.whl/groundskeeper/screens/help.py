"""Help screen showing all keybindings."""

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical, VerticalScroll
from textual.screen import ModalScreen
from textual.widgets import Static

KEYBINDINGS = """
[bold $primary]Session[/]

  [bold]g[/]        Start session (go)
  [bold]p[/]        Pause running session
  [bold]r[/]        Resume paused session
  [bold]c[/]        Clear history
  [bold]x[/]        Archive & deactivate

[bold $primary]Navigation[/]

  [bold]s[/]        Browse specs
  [bold]n[/]        Create new spec
  [bold]e[/]        Edit active spec
  [bold]a[/]        View archives
  [bold]l[/]        View logs
  [bold]h[/]        View history

[bold $primary]Application[/]

  [bold]q[/]        Quit
  [bold],[/]        Settings
  [bold]u[/]        Update (when available)
  [bold]?[/]        Show this help

[bold $primary]Lists & Screens[/]

  [bold]j[/] [bold]k[/]      Navigate up/down
  [bold]enter[/]    Select item
  [bold]e[/]        Edit spec
  [bold]d[/]        Delete item
  [bold]esc[/]      Close screen
"""


class HelpScreen(ModalScreen[None]):
    """Modal screen displaying all keybindings."""

    BINDINGS = [
        Binding("escape", "dismiss", "Close"),
        Binding("?", "dismiss", "Close", show=False),
        Binding("q", "dismiss", "Close", show=False),
        Binding("j", "scroll_down", "Down", show=False),
        Binding("k", "scroll_up", "Up", show=False),
    ]

    DEFAULT_CSS = """
    HelpScreen {
        align: center middle;
        background: $background 60%;
    }

    HelpScreen > Vertical {
        width: 54;
        min-width: 54;
        max-width: 54;
        height: auto;
        max-height: 80%;
        background: $surface;
        border: round $primary 50%;
        padding: 1 1;
    }

    HelpScreen .title {
        text-align: center;
        color: $text;
        text-style: bold;
        margin-bottom: 1;
        width: 100%;
    }

    HelpScreen #scroll {
        width: 100%;
        height: auto;
        max-height: 100%;
    }

    HelpScreen #content {
        width: 100%;
        height: auto;
        padding: 0;
    }

    HelpScreen .hint {
        text-align: center;
        color: $text-muted;
        margin-top: 1;
        width: 100%;
    }
    """

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Static("Keybindings", classes="title")
            with VerticalScroll(id="scroll"):
                yield Static(KEYBINDINGS.strip(), id="content")
            yield Static("esc close", classes="hint")

    def action_scroll_down(self) -> None:
        self.query_one("#scroll", VerticalScroll).scroll_down()

    def action_scroll_up(self) -> None:
        self.query_one("#scroll", VerticalScroll).scroll_up()
