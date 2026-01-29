"""Settings screen for viewing and editing application settings."""

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical, VerticalScroll
from textual.screen import ModalScreen
from textual.widgets import Checkbox, Input, Select, Static

from groundskeeper.settings import INPUT_TYPES, Setting


class SettingsScreen(ModalScreen[None]):
    """Modal screen for viewing and editing settings."""

    BINDINGS = [
        Binding("escape", "dismiss", "Close"),
        Binding("comma", "dismiss", "Close", show=False),
        Binding("q", "dismiss", "Close", show=False),
        Binding("j", "scroll_down", "Down", show=False),
        Binding("k", "scroll_up", "Up", show=False),
    ]

    DEFAULT_CSS = """
    SettingsScreen {
        align: center middle;
        background: $background 60%;
    }

    SettingsScreen > Vertical {
        width: 70;
        min-width: 70;
        max-width: 70;
        height: auto;
        max-height: 85%;
        background: $surface;
        border: round $primary 50%;
        padding: 1 2;
    }

    SettingsScreen .title {
        text-align: center;
        color: $text;
        text-style: bold;
        margin-bottom: 1;
        width: 100%;
    }

    SettingsScreen #scroll {
        width: 100%;
        height: auto;
        max-height: 100%;
    }

    SettingsScreen .section-title {
        color: $primary;
        text-style: bold;
        margin-top: 1;
        margin-bottom: 0;
    }

    SettingsScreen .setting-row {
        width: 100%;
        height: auto;
        margin: 0;
        padding: 0 0 0 2;
    }

    SettingsScreen .setting-label {
        color: $text;
        margin-bottom: 0;
    }

    SettingsScreen .setting-help {
        color: $text-muted;
        margin-bottom: 0;
    }

    SettingsScreen Select {
        width: 100%;
        margin-bottom: 1;
    }

    SettingsScreen Input {
        width: 100%;
        margin-bottom: 1;
    }

    SettingsScreen Checkbox {
        margin-bottom: 1;
    }

    SettingsScreen .hint {
        text-align: center;
        color: $text-muted;
        margin-top: 1;
        width: 100%;
    }
    """

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Static("Settings", classes="title")
            with VerticalScroll(id="scroll"):
                yield from self._build_settings_widgets()
            yield Static("esc close", classes="hint")

    def _build_settings_widgets(self) -> ComposeResult:
        """Build widgets for all settings from schema."""
        settings_map = self.app.settings.schema.settings_map

        for _section_key, section in settings_map.items():
            if section.type == "object" and section.children:
                yield Static(section.title, classes="section-title")
                for _setting_key, setting in section.children.items():
                    yield from self._build_setting_widget(setting)

    def _build_setting_widget(self, setting: Setting) -> ComposeResult:
        """Build a widget for a single setting."""
        if setting.type not in INPUT_TYPES:
            return

        current_value = self.app.settings.get(setting.key)

        with Vertical(classes="setting-row"):
            if setting.type == "boolean":
                yield Checkbox(
                    setting.title,
                    value=bool(current_value),
                    id=f"setting-{setting.key.replace('.', '-')}",
                )
                if setting.help:
                    yield Static(setting.help, classes="setting-help")
            elif setting.type == "choices" and setting.choices:
                yield Static(setting.title, classes="setting-label")
                if setting.help:
                    yield Static(setting.help, classes="setting-help")
                # Build options list
                options: list[tuple[str, str]] = []
                for choice in setting.choices:
                    if isinstance(choice, tuple):
                        options.append(choice)
                    else:
                        options.append((choice, choice))
                yield Select(
                    options=options,
                    value=str(current_value) if current_value else str(setting.default),
                    id=f"setting-{setting.key.replace('.', '-')}",
                )
            elif setting.type == "integer":
                yield Static(setting.title, classes="setting-label")
                if setting.help:
                    yield Static(setting.help, classes="setting-help")
                yield Input(
                    value=str(current_value) if current_value is not None else "",
                    placeholder=str(setting.default) if setting.default else "",
                    type="integer",
                    id=f"setting-{setting.key.replace('.', '-')}",
                )

    def on_checkbox_changed(self, event: Checkbox.Changed) -> None:
        """Handle checkbox changes."""
        widget_id = event.checkbox.id
        if widget_id and widget_id.startswith("setting-"):
            key = widget_id.replace("setting-", "").replace("-", ".")
            self.app.settings.set(key, event.value)
            self._save_settings()

    def on_select_changed(self, event: Select.Changed) -> None:
        """Handle select changes."""
        widget_id = event.select.id
        if widget_id and widget_id.startswith("setting-"):
            key = widget_id.replace("setting-", "").replace("-", ".")
            self.app.settings.set(key, event.value)
            self._save_settings()

    def on_input_changed(self, event: Input.Changed) -> None:
        """Handle input changes."""
        widget_id = event.input.id
        if widget_id and widget_id.startswith("setting-"):
            key = widget_id.replace("setting-", "").replace("-", ".")
            try:
                value = int(event.value) if event.value else 0
                self.app.settings.set(key, value)
                self._save_settings()
            except ValueError:
                pass  # Invalid integer input, ignore

    def _save_settings(self) -> None:
        """Save settings to disk if changed."""
        if self.app.settings.changed:
            settings_path = self.app._gk_dir / "settings.json"
            settings_path.write_text(self.app.settings.json, encoding="utf-8")
            self.app.settings.up_to_date()

    def action_scroll_down(self) -> None:
        self.query_one("#scroll", VerticalScroll).scroll_down()

    def action_scroll_up(self) -> None:
        self.query_one("#scroll", VerticalScroll).scroll_up()
