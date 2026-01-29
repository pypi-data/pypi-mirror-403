from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from textual.message import Message
from textual.screen import ModalScreen
from textual.widgets import OptionList, Static
from textual.widgets.option_list import Option

from groundskeeper.state import ArchivedSession


class ArchiveDeleteRequest(Message):
    """Request to delete an archived session."""

    def __init__(self, archive: ArchivedSession) -> None:
        super().__init__()
        self.archive = archive


class ArchiveScreen(ModalScreen[None]):
    """Browse and delete archived sessions."""

    BINDINGS = [
        Binding("d", "delete", "Delete"),
        Binding("escape", "dismiss", "Close"),
        Binding("j", "cursor_down", "Down", show=False),
        Binding("k", "cursor_up", "Up", show=False),
    ]

    DEFAULT_CSS = """
    ArchiveScreen { align: center middle; }
    ArchiveScreen > Vertical {
        width: 70%;
        height: 60%;
        background: #1a1a1a;
        border: solid #333333;
        padding: 1;
    }
    ArchiveScreen .title { dock: top; height: 1; color: #666666; }
    ArchiveScreen OptionList { height: 1fr; background: #1a1a1a; }
    ArchiveScreen OptionList:focus { border: none; }
    ArchiveScreen OptionList > .option-list--option-highlighted {
        background: #333333;
    }
    ArchiveScreen .hint { dock: bottom; height: 1; color: #666666; }
    ArchiveScreen .empty { color: #666666; text-style: italic; padding: 1; }
    """

    def __init__(self, archives: list[ArchivedSession]) -> None:
        super().__init__()
        self._archives = archives

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Static("─ archived sessions ─", classes="title")
            if self._archives:
                yield OptionList(*self._build_options(), id="archive-list")
            else:
                yield Static("No archived sessions found.", classes="empty")
            yield Static("↑↓ select · d delete · esc close", classes="hint")

    def _build_options(self) -> list[Option]:
        options: list[Option] = []
        for archive in self._archives:
            label = f"  {archive.name:<30} {archive.passed}/{archive.total} stories"
            options.append(Option(label, id=archive.name))
        return options

    def _get_selected_archive(self) -> ArchivedSession | None:
        if not self._archives:
            return None
        option_list = self.query_one("#archive-list", OptionList)
        idx = option_list.highlighted
        if idx is not None and 0 <= idx < len(self._archives):
            return self._archives[idx]
        return None

    def action_delete(self) -> None:
        archive = self._get_selected_archive()
        if archive:
            self.app.post_message(ArchiveDeleteRequest(archive))

    def action_cursor_down(self) -> None:
        if self._archives:
            self.query_one("#archive-list", OptionList).action_cursor_down()

    def action_cursor_up(self) -> None:
        if self._archives:
            self.query_one("#archive-list", OptionList).action_cursor_up()
