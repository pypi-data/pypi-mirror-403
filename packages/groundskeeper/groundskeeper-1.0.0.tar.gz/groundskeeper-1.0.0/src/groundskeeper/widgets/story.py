"""Clean story panel widget with subtle styling."""

from textual.app import ComposeResult
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Static


class StoryPanel(Widget):
    """Displays current story with minimal, elegant styling."""

    DEFAULT_CSS = """
    StoryPanel {
        height: auto;
        min-height: 3;
        padding: 0;
        margin: 1 0;
    }

    StoryPanel #content {
        color: $text;
        opacity: 0;
        transition: opacity 250ms;
    }

    StoryPanel #content.visible {
        opacity: 1;
    }

    StoryPanel .empty {
        color: $text-muted;
        text-style: italic;
    }
    """

    story_id: reactive[str] = reactive("")
    title: reactive[str] = reactive("")
    criteria: reactive[list[tuple[str, bool]]] = reactive(list)
    current_index: reactive[int] = reactive(0)

    def compose(self) -> ComposeResult:
        yield Static("", id="content")

    def watch_story_id(self) -> None:
        self._update()

    def watch_title(self) -> None:
        self._update()

    def watch_criteria(self) -> None:
        self._update()

    def watch_current_index(self) -> None:
        self._update()

    def _update(self) -> None:
        if not self.is_mounted:
            return

        content = self.query_one("#content", Static)

        # Handle empty states
        if not self.story_id:
            if self.title == "complete":
                content.update("[dim]all stories complete[/]")
                content.add_class("empty")
            elif self.title == "no spec":
                content.update("[dim]no spec loaded  [bold]n[/] new  [bold]s[/] browse[/]")
                content.add_class("empty")
            else:
                content.update("")
                content.add_class("empty")
            self._fade_in()
            return

        content.remove_class("empty")

        # Build clean layout
        lines = []

        # Header: story id and title
        lines.append(f"[$primary]{self.story_id}[/]  {self.title}")
        lines.append("")

        # Criteria list with minimal indicators
        for idx, (criterion, is_done) in enumerate(self.criteria):
            if is_done:
                lines.append(f"  [$success]>[/] [dim]{criterion}[/]")
            elif idx == self.current_index:
                lines.append(f"  [$primary]>[/] {criterion}")
            else:
                lines.append(f"  [dim]>[/] [dim]{criterion}[/]")

        content.update("\n".join(lines))
        self._fade_in()

    def _fade_in(self) -> None:
        content = self.query_one("#content", Static)
        content.remove_class("visible")
        self.call_after_refresh(lambda: content.add_class("visible"))
