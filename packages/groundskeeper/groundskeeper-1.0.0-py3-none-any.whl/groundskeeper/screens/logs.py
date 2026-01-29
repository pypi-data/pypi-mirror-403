from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from textual.screen import ModalScreen
from textual.widgets import Static, TextArea


class LogsScreen(ModalScreen[None]):
    BINDINGS = [
        Binding("escape", "dismiss", "Close"),
        Binding("j", "scroll_down", "Down", show=False),
        Binding("k", "scroll_up", "Up", show=False),
    ]

    DEFAULT_CSS = """
    LogsScreen { align: center middle; }
    LogsScreen > Vertical {
        width: 90%;
        height: 80%;
        background: #1a1a1a;
        border: solid #333333;
        padding: 1;
    }
    LogsScreen .title { dock: top; height: 1; color: #666666; }
    LogsScreen TextArea { height: 1fr; background: #1a1a1a; }
    LogsScreen .hint { dock: bottom; height: 1; color: #666666; }
    """

    def __init__(self, content: str) -> None:
        super().__init__()
        self._content = content

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Static("─ logs ─", classes="title")
            yield TextArea(self._content, read_only=True, id="content")
            yield Static("↑↓ scroll · esc close", classes="hint")

    def action_scroll_down(self) -> None:
        self.query_one("#content", TextArea).scroll_down()

    def action_scroll_up(self) -> None:
        self.query_one("#content", TextArea).scroll_up()
