"""Spec editing screen with JSON validation."""

import json

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from textual.reactive import reactive
from textual.screen import ModalScreen
from textual.widgets import Static, TextArea

from groundskeeper.state import Spec


class EditSpecScreen(ModalScreen[dict | None]):
    """Modal screen for editing spec JSON with validation."""

    BINDINGS = [
        Binding("ctrl+s", "save", "Save", show=True),
        Binding("ctrl+v", "validate", "Validate", show=True),
        Binding("escape", "cancel", "Cancel", priority=True),
    ]

    DEFAULT_CSS = """
    EditSpecScreen {
        align: center middle;
    }
    EditSpecScreen > Vertical {
        width: 85%;
        height: 90%;
        background: $surface;
        border: round $primary 50%;
        padding: 1 2;
    }
    EditSpecScreen .title {
        dock: top;
        height: 1;
        color: $primary;
        text-style: bold;
        margin-bottom: 1;
    }
    EditSpecScreen TextArea {
        height: 1fr;
        background: $background;
        border: round $border 30%;
    }
    EditSpecScreen TextArea:focus {
        border: round $primary 60%;
    }
    EditSpecScreen .status {
        dock: bottom;
        height: 1;
        color: $text-muted;
        margin-top: 1;
    }
    EditSpecScreen .status.-valid {
        color: $success;
    }
    EditSpecScreen .status.-invalid {
        color: $error;
    }
    EditSpecScreen .hint {
        dock: bottom;
        height: 1;
        color: $text-muted;
    }
    """

    validation_status: reactive[str] = reactive("")
    is_valid: reactive[bool] = reactive(True)

    def __init__(self, spec: Spec, json_content: str) -> None:
        super().__init__()
        self._spec = spec
        self._json_content = json_content

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Static(f"─ edit: {self._spec.name} ─", classes="title")
            yield TextArea(self._json_content, id="editor", language="json", theme="monokai")
            yield Static("", classes="status", id="status")
            yield Static("ctrl+s save · ctrl+v validate · esc cancel", classes="hint")

    def on_mount(self) -> None:
        self.query_one("#editor", TextArea).focus()

    def watch_validation_status(self) -> None:
        status_widget = self.query_one("#status", Static)
        status_widget.update(self.validation_status)
        status_widget.remove_class("-valid", "-invalid")
        if self.validation_status:
            status_widget.add_class("-valid" if self.is_valid else "-invalid")

    def _validate_json(self) -> tuple[bool, str, dict | None]:
        """Validate the JSON in the editor.

        Returns:
            Tuple of (is_valid, error_message, parsed_dict)
        """
        editor = self.query_one("#editor", TextArea)
        json_str = editor.text

        try:
            parsed = json.loads(json_str)
        except json.JSONDecodeError as e:
            return False, f"JSON syntax error: {e.msg} (line {e.lineno})", None

        # Check required fields
        required_fields = ["project", "userStories"]
        missing = [f for f in required_fields if f not in parsed]
        if missing:
            return False, f"Missing required fields: {', '.join(missing)}", None

        # Validate userStories structure
        stories = parsed.get("userStories", [])
        if not isinstance(stories, list):
            return False, "userStories must be an array", None

        for i, story in enumerate(stories):
            if not isinstance(story, dict):
                return False, f"Story {i + 1} must be an object", None
            if "id" not in story:
                return False, f"Story {i + 1} missing 'id' field", None
            if "title" not in story:
                return False, f"Story {i + 1} missing 'title' field", None

        return True, "Valid spec JSON", parsed

    def action_validate(self) -> None:
        """Validate the JSON without saving."""
        is_valid, message, _ = self._validate_json()
        self.is_valid = is_valid
        self.validation_status = message

    def action_save(self) -> None:
        """Validate and save if valid."""
        is_valid, message, parsed = self._validate_json()
        self.is_valid = is_valid
        self.validation_status = message

        if is_valid and parsed:
            self.dismiss(parsed)

    def action_cancel(self) -> None:
        """Cancel without saving."""
        self.dismiss(None)
