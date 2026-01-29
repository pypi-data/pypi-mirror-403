"""Confirmation dialog screens with adaptive theming."""

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from textual.screen import ModalScreen
from textual.widgets import Static

from groundskeeper.state import ArchivedSession, Spec


class ConfirmScreen(ModalScreen[bool]):
    """Generic confirmation dialog."""

    BINDINGS = [
        Binding("y", "confirm", "Yes"),
        Binding("n", "cancel", "No"),
        Binding("escape", "cancel", "Cancel"),
    ]

    def __init__(self, title: str, message: str) -> None:
        super().__init__()
        self._title = title
        self._message = message

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Static(f"─ {self._title} ─", classes="title")
            yield Static(self._message, classes="message")
            yield Static("y confirm · n cancel", classes="hint")

    def action_confirm(self) -> None:
        self.dismiss(True)

    def action_cancel(self) -> None:
        self.dismiss(False)


class DeleteSpecConfirmScreen(ConfirmScreen):
    """Confirmation dialog for deleting a spec."""

    def __init__(self, spec: Spec) -> None:
        super().__init__(
            "delete spec?",
            f"Delete spec '{spec.name}'?\nThis cannot be undone.",
        )


class ClearHistoryConfirmScreen(ConfirmScreen):
    """Confirmation dialog for clearing session history."""

    def __init__(self) -> None:
        super().__init__(
            "clear history?",
            "Clear session history (progress.txt)?\nSpec will remain active. This cannot be undone.",
        )


class DeleteArchiveConfirmScreen(ConfirmScreen):
    """Confirmation dialog for deleting an archived session."""

    def __init__(self, archive: ArchivedSession) -> None:
        super().__init__(
            "delete archive?",
            f"Delete archived session '{archive.name}'?\nThis cannot be undone.",
        )


class ArchiveSessionConfirmScreen(ConfirmScreen):
    """Confirmation dialog for archiving and deactivating the current session."""

    def __init__(self, spec_name: str) -> None:
        super().__init__(
            "archive session?",
            f"Archive '{spec_name}' and deactivate?\nSession will be saved to archives.",
        )


class QuitConfirmScreen(ConfirmScreen):
    """Confirmation dialog for quitting while running."""

    def __init__(self) -> None:
        super().__init__(
            "quit?",
            "Groundskeeper is still running.\nProgress will be saved.",
        )
