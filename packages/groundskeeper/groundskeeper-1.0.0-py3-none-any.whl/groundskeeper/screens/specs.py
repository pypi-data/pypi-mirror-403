from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from textual.message import Message
from textual.screen import ModalScreen
from textual.widgets import OptionList, Static
from textual.widgets.option_list import Option

from groundskeeper.state import Spec


class SpecDeleteRequest(Message):
    """Request to delete a spec."""

    def __init__(self, spec: Spec) -> None:
        super().__init__()
        self.spec = spec


class SpecEditRequest(Message):
    """Request to edit a spec."""

    def __init__(self, spec: Spec) -> None:
        super().__init__()
        self.spec = spec


class SpecsScreen(ModalScreen[Spec | None]):
    """Browse and select PRD specs."""

    BINDINGS = [
        Binding("enter", "activate", "Activate"),
        Binding("e", "edit", "Edit"),
        Binding("d", "delete", "Delete"),
        Binding("escape", "dismiss", "Close"),
        Binding("j", "cursor_down", "Down", show=False),
        Binding("k", "cursor_up", "Up", show=False),
    ]

    DEFAULT_CSS = """
    SpecsScreen { align: center middle; }
    SpecsScreen > Vertical {
        width: 70%;
        height: 60%;
        background: #1a1a1a;
        border: solid #333333;
        padding: 1;
    }
    SpecsScreen .title { dock: top; height: 1; color: #666666; }
    SpecsScreen OptionList { height: 1fr; background: #1a1a1a; }
    SpecsScreen OptionList:focus { border: none; }
    SpecsScreen OptionList > .option-list--option-highlighted {
        background: #333333;
    }
    SpecsScreen .hint { dock: bottom; height: 1; color: #666666; }
    SpecsScreen .empty { color: #666666; text-style: italic; padding: 1; }
    """

    def __init__(self, specs: list[Spec]) -> None:
        super().__init__()
        self._specs = specs

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Static("─ specs ─", classes="title")
            if self._specs:
                yield OptionList(*self._build_options(), id="spec-list")
            else:
                yield Static("No specs found. Press 'n' to create one.", classes="empty")
            yield Static(
                "↑↓ select · enter activate · e edit · d delete · esc close", classes="hint"
            )

    def _build_options(self) -> list[Option]:
        options: list[Option] = []
        for spec in self._specs:
            indicator = "●" if spec.is_active else " "
            label = (
                f"{indicator} {spec.name:<20} {spec.passed}/{spec.total} stories   [{spec.status}]"
            )
            options.append(Option(label, id=spec.name))
        return options

    def _get_selected_spec(self) -> Spec | None:
        if not self._specs:
            return None
        option_list = self.query_one("#spec-list", OptionList)
        idx = option_list.highlighted
        if idx is not None and 0 <= idx < len(self._specs):
            return self._specs[idx]
        return None

    def action_activate(self) -> None:
        spec = self._get_selected_spec()
        if spec:
            self.dismiss(spec)

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        """Handle Enter key on OptionList - activate the selected spec."""
        spec = self._get_selected_spec()
        if spec:
            self.dismiss(spec)

    def action_edit(self) -> None:
        spec = self._get_selected_spec()
        if spec:
            self.app.post_message(SpecEditRequest(spec))

    def action_delete(self) -> None:
        spec = self._get_selected_spec()
        if spec:
            if spec.is_active:
                self.app.notify("Cannot delete active spec", severity="warning")
            else:
                self.app.post_message(SpecDeleteRequest(spec))

    def action_cursor_down(self) -> None:
        if self._specs:
            self.query_one("#spec-list", OptionList).action_cursor_down()

    def action_cursor_up(self) -> None:
        if self._specs:
            self.query_one("#spec-list", OptionList).action_cursor_up()
