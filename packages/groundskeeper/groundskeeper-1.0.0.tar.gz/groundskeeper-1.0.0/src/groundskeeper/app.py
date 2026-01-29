import json
from collections import deque
from datetime import datetime
from functools import cached_property
from pathlib import Path

from textual import getters, work
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from textual.reactive import reactive
from textual.signal import Signal
from textual.timer import Timer
from textual.widgets import Footer

from groundskeeper.constants import ITERATION_DELAY, MAX_OUTPUT_LINES, PAUSE_CHECK_INTERVAL
from groundskeeper.parser import parse_history, parse_prd
from groundskeeper.runner import BackendType, run_iteration
from groundskeeper.screens import (
    ArchiveDeleteRequest,
    ArchiveScreen,
    ArchiveSessionConfirmScreen,
    ClearHistoryConfirmScreen,
    DeleteArchiveConfirmScreen,
    DeleteSpecConfirmScreen,
    EditSpecScreen,
    HelpScreen,
    HistoryScreen,
    LogsScreen,
    NewSpecScreen,
    QuitConfirmScreen,
    SettingsScreen,
    SpecDeleteRequest,
    SpecEditRequest,
    SpecsScreen,
)
from groundskeeper.settings import Schema, Settings
from groundskeeper.settings_schema import SCHEMA
from groundskeeper.specmanager import SpecManager
from groundskeeper.state import Spec, State, Status
from groundskeeper.version_check import VersionCheckResult, check_for_updates
from groundskeeper.watcher import watch_files
from groundskeeper.widgets import Header, Output, Progress, StoryPanel


class GroundskeeperApp(App):
    CSS_PATH = "groundskeeper.tcss"
    BINDINGS = [
        Binding("g", "start", "Go", tooltip="Start the agent loop"),
        Binding("p", "pause", "Pause", tooltip="Pause the running agent"),
        Binding("r", "resume", "Resume", tooltip="Resume paused agent"),
        Binding("c", "clear_history", "Clear", tooltip="Clear session history"),
        Binding("s", "specs", "Specs", tooltip="Browse and select specs"),
        Binding("n", "new_spec", "New", tooltip="Create a new spec"),
        Binding("e", "edit_spec", "Edit", tooltip="Edit active spec"),
        Binding("a", "archives", "Archives", tooltip="View archived sessions"),
        Binding("l", "logs", "Logs", tooltip="View session logs"),
        Binding("h", "history", "History", tooltip="View iteration history"),
        Binding("x", "archive_session", "Archive", tooltip="Archive current session"),
        Binding("comma", "settings", "Settings", tooltip="Open settings"),
        Binding("question_mark", "help", "Help", tooltip="Show help"),
        Binding("f1", "toggle_help_panel", "Help Panel", show=False),
        Binding("q", "quit_app", "Quit", tooltip="Quit the application"),
    ]

    # Register command palette provider
    @property
    def COMMANDS(self) -> set[type]:  # noqa: N802
        from groundskeeper.providers import GroundskeeperProvider

        return {GroundskeeperProvider}

    # Getter descriptors for common widget queries
    header_widget = getters.query_one(Header)
    progress_widget = getters.query_one(Progress)
    story_panel = getters.query_one(StoryPanel)
    output_widget = getters.query_one(Output)

    state: reactive[State] = reactive(State, recompose=False)
    settings_changed: Signal[tuple[str, object]]

    @cached_property
    def settings_schema(self) -> Schema:
        """Get the settings schema.

        Returns:
            Schema instance for settings validation.
        """
        return Schema(SCHEMA)

    @cached_property
    def settings(self) -> Settings:
        """Get the settings instance.

        Returns:
            Settings instance with callback wired up.
        """
        return Settings(self.settings_schema, self._settings_dict, on_set_callback=self.on_setting)

    def on_setting(self, key: str, value: object) -> None:
        """Handle setting changes by toggling CSS classes and applying themes.

        Args:
            key: Setting key in dot notation (e.g., "ui.compact-output").
            value: New value for the setting.
        """
        match key:
            case "ui.compact-output":
                self.set_class(bool(value), "compact-output")
            case "ui.show-quotes":
                # This could be used to toggle a quotes widget if implemented
                pass
            case "ui.theme":
                # Apply Textual's built-in theme if not "terminal"
                if isinstance(value, str) and value != "terminal":
                    self.theme = value
        # Publish settings change signal
        self.settings_changed.publish((key, value))

    def __init__(
        self,
        max_iterations: int = 10,
        prd_path: Path | None = None,
        groundskeeper_dir: Path | None = None,
        backend: BackendType = "claude",
    ) -> None:
        super().__init__()
        self._gk_dir = groundskeeper_dir or Path.cwd() / ".groundskeeper"
        self._spec_manager = SpecManager(self._gk_dir)
        self._backend: BackendType = backend
        self._settings_dict: dict[str, object] = {}

        # Initialize signal for settings changes
        self.settings_changed = Signal(self, "settings-changed")

        workspace = Path.cwd()
        self.state = State(
            max_iterations=max_iterations,
            workspace=workspace,
            groundskeeper_dir=self._gk_dir,
        )

        # Determine PRD path
        if prd_path:
            self._prd_path = prd_path
        else:
            self._prd_path = self._spec_manager.get_active_prd_path()

        self._progress_path = self._spec_manager.get_active_progress_path()
        self._session_start: datetime | None = None
        self._elapsed_timer: Timer | None = None
        self._watcher_stop_requested = False
        self._output_buffer: deque[str] = deque(maxlen=MAX_OUTPUT_LINES)
        self._version_check_result: VersionCheckResult | None = None

    def compose(self) -> ComposeResult:
        yield Header()
        with Vertical(id="main"):
            yield Progress()
            yield StoryPanel()
            yield Output()
        yield Footer()

    async def on_mount(self) -> None:
        self._spec_manager.ensure_structure()

        # Load settings from file or initialize with defaults
        settings_path = self._gk_dir / "settings.json"
        try:
            self._settings_dict = (
                json.loads(settings_path.read_text(encoding="utf-8"))
                if settings_path.exists()
                else {}
            )
        except (json.JSONDecodeError, OSError):
            self._settings_dict = {}

        # Initialize all settings to apply CSS classes
        self.settings.set_all()

        self._load_state()
        # Update UI after widgets are fully mounted
        self.call_after_refresh(self._update_ui)
        self._session_start = datetime.now()

        # Use set_interval for elapsed time updates (replaces async loop)
        self._elapsed_timer = self.set_interval(1, self._update_elapsed)

        # Start file watcher using @work decorator
        self._start_watcher()

        # Check for updates in the background
        self._check_for_updates()

    @work(thread=True, exit_on_error=False)
    async def _check_for_updates(self) -> None:
        """Check for updates asynchronously and notify if available."""
        result = check_for_updates()
        self._version_check_result = result

        # Show notification if update is available
        if result.update_available and result.latest_version:
            self.call_from_thread(
                self.notify,
                f"v{result.latest_version} available: uv tool upgrade groundskeeper",
                title="Update Available",
                timeout=10,
            )

    def _load_state(self) -> None:
        self.state.stories = parse_prd(self._prd_path)
        self.state.history = parse_history(self._progress_path)
        self.state.specs = self._spec_manager.list_specs()
        self.state.active_spec = self._spec_manager.get_active()

    @work(exit_on_error=False, group="watcher")
    async def _start_watcher(self) -> None:
        """Start file watcher for prd.json and progress.txt changes."""
        import asyncio

        stop_event = asyncio.Event()
        self._watcher_stop_event = stop_event
        self._watcher_stop_requested = False
        await watch_files(
            prd_path=self._prd_path,
            progress_path=self._progress_path,
            on_prd_change=self._on_prd_change,
            on_progress_change=self._on_progress_change,
            stop_event=stop_event,
        )

    def _on_prd_change(self) -> None:
        """Handle prd.json file changes."""
        self.state.stories = parse_prd(self._prd_path)
        self._update_ui()

    def _on_progress_change(self) -> None:
        """Handle progress.txt file changes."""
        self.state.history = parse_history(self._progress_path)
        self._update_ui()

    async def _restart_watcher(self) -> None:
        """Restart the file watcher with current paths."""
        # Signal the old watcher to stop
        if hasattr(self, "_watcher_stop_event"):
            self._watcher_stop_event.set()
        # Cancel the watcher worker group
        self.workers.cancel_group(self, "watcher")
        # Start a new watcher
        self._start_watcher()

    def _update_ui(self) -> None:
        # Use getter descriptors for cleaner widget access
        self.header_widget.spec_name = self.state.spec_name
        self.header_widget.iteration = self.state.current_iteration
        self.header_widget.max_iterations = self.state.max_iterations
        self.header_widget.status = self.state.status

        self.progress_widget.completed = self.state.completed_count
        self.progress_widget.total = self.state.total_count
        self.progress_widget.is_active = self.state.status == Status.RUNNING

        if story := self.state.current_story:
            self.story_panel.story_id = story.id
            self.story_panel.title = story.title
            # Convert criteria to (text, is_done) tuples - all pending for now
            self.story_panel.criteria = [(c, False) for c in story.acceptance_criteria]
            self.story_panel.current_index = 0
        elif self.state.status == Status.COMPLETE:
            self.story_panel.story_id = ""
            self.story_panel.title = "complete"
            self.story_panel.criteria = []
        elif not self.state.stories:
            self.story_panel.story_id = ""
            self.story_panel.title = "no spec"
            self.story_panel.criteria = []
            self.story_panel.current_index = 0
        else:
            self.story_panel.story_id = ""
            self.story_panel.title = ""
            self.story_panel.criteria = []

        self.output_widget.is_live = self.state.status == Status.RUNNING

    def _update_elapsed(self) -> None:
        """Update elapsed time display (called by set_interval timer)."""
        if self._session_start:
            elapsed = datetime.now() - self._session_start
            mins, secs = divmod(int(elapsed.total_seconds()), 60)
            self.header_widget.elapsed = f"{mins:02d}:{secs:02d}"

    @work(exclusive=True, group="agent")
    async def _run_loop(self) -> None:
        import asyncio

        self.state.status = Status.RUNNING
        self._update_ui()

        if not self._prd_path.exists():
            self._write_output(f"Error: {self._prd_path} not found\n")
            self._write_output("Press 's' to browse specs or 'n' to create a new one.\n")
            self.state.status = Status.IDLE
            self._update_ui()
            return

        try:
            while self.state.current_iteration < self.state.max_iterations:
                if self.state.status == Status.PAUSED:
                    await asyncio.sleep(PAUSE_CHECK_INTERVAL)
                    continue

                if self.state.status != Status.RUNNING:
                    break

                self.state.current_iteration += 1
                self._update_ui()

                self._write_output(f"\n{'=' * 50}\n")
                self._write_output(
                    f"Iteration {self.state.current_iteration}/{self.state.max_iterations}\n"
                )
                self._write_output(f"{'=' * 50}\n")

                status, _ = await run_iteration(
                    self.state.workspace,
                    self._write_output,
                    backend=self._backend,
                    is_paused=lambda: self.state.status == Status.PAUSED,
                )

                self._load_state()
                self._update_ui()

                if status == Status.COMPLETE:
                    self.state.status = Status.COMPLETE
                    break
                if status == Status.ERROR:
                    self.state.status = Status.ERROR
                    break

                await asyncio.sleep(ITERATION_DELAY)

            if self.state.current_iteration >= self.state.max_iterations:
                self.state.status = Status.ERROR
                self._write_output("\nMax iterations reached.\n")

        except asyncio.CancelledError:
            self._write_output("\n[Cancelled]\n")
            raise
        finally:
            self._update_ui()

    def _write_output(self, text: str) -> None:
        self._output_buffer.append(text)
        self.output_widget.write(text)

    def action_quit_app(self) -> None:
        if self.state.status == Status.RUNNING:
            self.push_screen(QuitConfirmScreen(), self._handle_quit)
        else:
            self.exit()

    def _handle_quit(self, confirmed: bool | None) -> None:
        if confirmed:
            # Cancel agent worker group
            self.workers.cancel_group(self, "agent")
            # Stop elapsed timer
            if self._elapsed_timer:
                self._elapsed_timer.stop()
            # Stop watcher
            if hasattr(self, "_watcher_stop_event"):
                self._watcher_stop_event.set()
            self.workers.cancel_group(self, "watcher")
            self.exit()

    def action_pause(self) -> None:
        if self.state.status == Status.RUNNING:
            self.state.status = Status.PAUSED
            self._write_output("\n[Paused]\n")
            self._update_ui()

    def action_resume(self) -> None:
        if self.state.status == Status.PAUSED:
            self.state.status = Status.RUNNING
            self._write_output("\n[Resumed]\n")
            self._update_ui()
        elif self.state.status == Status.IDLE:
            # Resume also works from IDLE state (same as start)
            self._write_output("\n[Starting session]\n")
            self._run_loop()

    def action_start(self) -> None:
        """Start session from IDLE state."""
        if self.state.status == Status.IDLE:
            self._write_output("\n[Starting session]\n")
            self._run_loop()
        # If already running, do nothing

    def action_specs(self) -> None:
        self.state.specs = self._spec_manager.list_specs()

        def on_spec_selected(spec: Spec | None) -> None:
            if spec:
                asyncio.create_task(self._handle_spec_selected(spec))

        self.push_screen(SpecsScreen(self.state.specs), on_spec_selected)

    async def _handle_spec_selected(self, spec: Spec | None) -> None:
        if spec:
            self._spec_manager.activate(spec)
            self._prd_path = self._spec_manager.get_active_prd_path()
            self._progress_path = self._spec_manager.get_active_progress_path()
            self._load_state()
            self._update_ui()
            self._write_output(f"\nActivated spec: {spec.name}\n")

            # Restart watcher with new paths
            await self._restart_watcher()

    def on_spec_delete_request(self, message: SpecDeleteRequest) -> None:
        spec = message.spec
        if spec.is_active:
            self.notify("Cannot delete active spec", severity="warning")
            return

        def on_confirm(confirmed: bool | None) -> None:
            if confirmed:
                self._spec_manager.delete_spec(spec)
                self.notify(f"Deleted: {spec.name}")
                # Refresh specs list and reopen the specs screen
                self.state.specs = self._spec_manager.list_specs()
                self.pop_screen()  # Close current SpecsScreen

                def on_spec_selected(new_spec: Spec | None) -> None:
                    if new_spec:
                        asyncio.create_task(self._handle_spec_selected(new_spec))

                self.push_screen(SpecsScreen(self.state.specs), on_spec_selected)

        self.push_screen(DeleteSpecConfirmScreen(spec), on_confirm)

    def action_new_spec(self) -> None:
        self.push_screen(
            NewSpecScreen(self._gk_dir),
            self._handle_new_spec,
        )

    def _handle_new_spec(self, path: Path | None) -> None:
        if path:
            # Load and activate the new spec
            self._load_state()
            for spec in self.state.specs:
                if spec.path == path:
                    self._spec_manager.activate(spec)
                    break
            self._prd_path = self._spec_manager.get_active_prd_path()
            self._progress_path = self._spec_manager.get_active_progress_path()
            self._load_state()
            self._update_ui()

    def action_edit_spec(self) -> None:
        """Edit the active spec."""
        if not self.state.active_spec:
            self.notify("No active spec to edit", severity="warning")
            return

        self._open_edit_screen(self.state.active_spec)

    def on_spec_edit_request(self, message: SpecEditRequest) -> None:
        """Handle edit request from SpecsScreen."""
        self._open_edit_screen(message.spec)

    def _open_edit_screen(self, spec: Spec) -> None:
        """Open the edit screen for a spec."""
        try:
            json_content = spec.path.read_text(encoding="utf-8")
            # Ensure it's properly formatted
            parsed = json.loads(json_content)
            formatted = json.dumps(parsed, indent=2)
        except (json.JSONDecodeError, OSError) as e:
            self.notify(f"Could not read spec: {e}", severity="error")
            return

        def on_edit_complete(result: dict | None) -> None:
            if result:
                asyncio.create_task(self._handle_spec_edited(spec, result))

        self.push_screen(EditSpecScreen(spec, formatted), on_edit_complete)

    async def _handle_spec_edited(self, spec: Spec, prd_data: dict) -> None:
        """Handle spec edit completion."""
        try:
            self._spec_manager.update_spec(spec.path, prd_data)
            self.notify(f"Saved: {spec.name}")
            # Reload state to reflect changes
            self._load_state()
            self._update_ui()
            # Restart watcher in case paths changed
            await self._restart_watcher()
        except ValueError as e:
            self.notify(f"Save failed: {e}", severity="error")

    def action_logs(self) -> None:
        content = "".join(self._output_buffer)
        self.push_screen(LogsScreen(content))

    def action_history(self) -> None:
        self.push_screen(HistoryScreen(self.state.history))

    def action_clear_history(self) -> None:
        """Clear session history with confirmation."""
        if not self.state.active_spec:
            self.notify("No active spec to clear history for", severity="warning")
            return

        def on_confirm(confirmed: bool | None) -> None:
            if confirmed:
                self._spec_manager.clear_history()
                # Reset iteration counter
                self.state.current_iteration = 0
                self.state.status = Status.IDLE
                # Clear output buffer and log
                self._output_buffer.clear()
                self.query_one(Output).clear()
                # Reload state and update UI
                self._load_state()
                self._update_ui()
                self.notify("Session cleared")

        self.push_screen(ClearHistoryConfirmScreen(), on_confirm)

    def action_archive_session(self) -> None:
        """Archive current session and deactivate spec."""
        if not self.state.active_spec:
            self.notify("No active session to archive", severity="warning")
            return

        if self.state.status == Status.RUNNING:
            self.notify("Cannot archive while running. Pause first.", severity="warning")
            return

        spec_name = self.state.active_spec.name

        def on_confirm(confirmed: bool | None) -> None:
            if confirmed:
                asyncio.create_task(self._handle_archive_session(spec_name))

        self.push_screen(ArchiveSessionConfirmScreen(spec_name), on_confirm)

    async def _handle_archive_session(self, spec_name: str) -> None:
        """Handle archiving the current session."""
        # Archive the active session
        self._spec_manager.archive_active()

        # Clear state
        self.state.stories = []
        self.state.history = ""
        self.state.active_spec = None
        self.state.current_iteration = 0
        self.state.status = Status.IDLE

        # Clear output
        self._output_buffer.clear()
        self.query_one(Output).clear()

        # Update UI
        self._update_ui()

        # Restart watcher (will watch empty paths now)
        await self._restart_watcher()

        self.notify(f"Archived: {spec_name}")
        self._write_output(f"\nArchived session: {spec_name}\n")
        self._write_output("Press 's' to select a spec or 'n' to create a new one.\n")

    def action_archives(self) -> None:
        """Show archived sessions."""
        archives = self._spec_manager.list_archives()
        self.push_screen(ArchiveScreen(archives))

    def on_archive_delete_request(self, message: ArchiveDeleteRequest) -> None:
        archive = message.archive

        def on_confirm(confirmed: bool | None) -> None:
            if confirmed:
                self._spec_manager.delete_archive(archive)
                self.notify(f"Deleted: {archive.name}")
                # Refresh archive list and reopen the archive screen
                self.pop_screen()  # Close current ArchiveScreen
                archives = self._spec_manager.list_archives()
                self.push_screen(ArchiveScreen(archives))

        self.push_screen(DeleteArchiveConfirmScreen(archive), on_confirm)

    def action_settings(self) -> None:
        """Show settings screen."""
        self.push_screen(SettingsScreen())

    def action_help(self) -> None:
        """Show help screen with all keybindings."""
        self.push_screen(HelpScreen())

    def action_toggle_help_panel(self) -> None:
        """Toggle the built-in help panel (F1)."""
        self.action_toggle("help_panel")
