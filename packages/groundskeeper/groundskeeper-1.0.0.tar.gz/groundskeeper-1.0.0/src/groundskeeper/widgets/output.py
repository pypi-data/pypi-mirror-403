"""Clean output log widget with bordered frame matching StoryPanel."""

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import RichLog

from groundskeeper.ansi import ansi_to_rich, contains_ansi


class Output(Widget):
    """Output panel with bordered frame matching the story panel style."""

    DEFAULT_CSS = """
    Output {
        height: 1fr;
        background: transparent;
        padding: 0;
        margin: 0;
    }

    Output #frame {
        height: 100%;
        border: round $border 30%;
        border-title-color: $text-muted;
        border-title-style: none;
        background: transparent;
        padding: 0 1;
        margin: 0;
    }

    Output #frame.live {
        border: round $success 60%;
        border-title-color: $success;
    }

    Output RichLog {
        height: 1fr;
        background: transparent;
        scrollbar-color: $border 30%;
        scrollbar-color-hover: $primary 50%;
        scrollbar-size-vertical: 1;
        padding: 0;
        margin: 0;
    }
    """

    is_live: reactive[bool] = reactive(False)

    def compose(self) -> ComposeResult:
        with Vertical(id="frame"):
            yield RichLog(id="log", highlight=True, markup=True)

    def on_mount(self) -> None:
        """Set the border title after mounting."""
        frame = self.query_one("#frame", Vertical)
        frame.border_title = "output"

    def watch_is_live(self, is_live: bool) -> None:
        """Update frame styling when live status changes."""
        try:
            frame = self.query_one("#frame", Vertical)
            if is_live:
                frame.border_title = "output [dim]live[/]"
                frame.add_class("live")
            else:
                frame.border_title = "output"
                frame.remove_class("live")
        except Exception:
            pass

    def write(self, text: str) -> None:
        """Write text to the log, handling ANSI codes."""
        log = self.query_one("#log", RichLog)
        content = text.rstrip("\n")

        if contains_ansi(content):
            log.write(ansi_to_rich(content))
        else:
            log.write(content)

    def clear(self) -> None:
        self.query_one("#log", RichLog).clear()

    def get_text(self) -> str:
        log = self.query_one("#log", RichLog)
        return "\n".join(str(line) for line in log.lines)
