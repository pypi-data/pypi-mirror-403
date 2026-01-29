"""Groundskeeper-inspired header widget with logo and status indicators."""

from textual.app import ComposeResult
from textual.reactive import reactive
from textual.timer import Timer
from textual.widget import Widget
from textual.widgets import Static

from groundskeeper import __version__
from groundskeeper.constants import PULSE_INTERVAL
from groundskeeper.state import Status
from groundskeeper.widgets.logo import Logo

# Pulsing animation frames for running status
PULSE_FRAMES = ["running", "running", "RUNNING", "RUNNING"]


class Header(Widget):
    """Header with Groundskeeper logo and essential session info."""

    DEFAULT_CSS = """
    Header {
        height: 1;
        dock: top;
        layout: horizontal;
        background: transparent;
        padding: 0;
    }

    Header Logo {
        width: auto;
    }

    Header .sep {
        color: $text-muted;
        width: auto;
        margin: 0 1;
    }

    Header .spec {
        color: $text;
        width: auto;
    }

    Header .meta {
        color: $text-muted;
        width: auto;
    }

    Header .spacer {
        width: 1fr;
    }

    Header .status {
        width: auto;
        transition: color 200ms, opacity 200ms;
    }

    Header .status-idle {
        color: $text-muted;
    }

    Header .status-running {
        color: $success;
        text-style: bold;
    }

    Header .status-paused {
        color: $warning;
    }

    Header .status-complete {
        color: $success;
    }

    Header .status-error {
        color: $error;
    }

    Header .version {
        color: $text-muted;
        width: auto;
        margin-left: 1;
    }
    """

    spec_name: reactive[str] = reactive("")
    iteration: reactive[int] = reactive(0)
    max_iterations: reactive[int] = reactive(10)
    elapsed: reactive[str] = reactive("00:00")
    status: reactive[Status] = reactive(Status.IDLE)

    _pulse_timer: Timer | None = None
    _pulse_frame: int = 0

    def compose(self) -> ComposeResult:
        yield Logo(compact=True)
        yield Static("/", classes="sep")
        yield Static("", id="spec", classes="spec")
        yield Static("", id="meta", classes="meta")
        yield Static("", classes="spacer")
        yield Static("", id="status", classes="status")
        yield Static(f"v{__version__}", classes="version")

    def on_mount(self) -> None:
        self.call_after_refresh(self._update_all)
        # Start pulse timer for running animation
        self._pulse_timer = self.set_interval(PULSE_INTERVAL, self._pulse_tick)

    def on_unmount(self) -> None:
        if self._pulse_timer:
            self._pulse_timer.stop()

    def _pulse_tick(self) -> None:
        """Animate the running status indicator."""
        if self.status == Status.RUNNING:
            self._pulse_frame = (self._pulse_frame + 1) % len(PULSE_FRAMES)
            if self.is_mounted:
                status_widget = self.query_one("#status", Static)
                status_widget.update(PULSE_FRAMES[self._pulse_frame])

    def _update_all(self) -> None:
        self._update_spec()
        self._update_meta()
        self._update_status()

    def watch_spec_name(self) -> None:
        self._update_spec()

    def watch_iteration(self) -> None:
        self._update_meta()

    def watch_max_iterations(self) -> None:
        self._update_meta()

    def watch_elapsed(self) -> None:
        self._update_meta()

    def watch_status(self) -> None:
        self._update_status()

    def _update_spec(self) -> None:
        if not self.is_mounted:
            return
        spec = self.query_one("#spec", Static)
        spec.update(self.spec_name if self.spec_name else "no spec")

    def _update_meta(self) -> None:
        if not self.is_mounted:
            return
        meta = self.query_one("#meta", Static)
        meta.update(f"  {self.iteration}/{self.max_iterations}  {self.elapsed}")

    def _update_status(self) -> None:
        if not self.is_mounted:
            return
        status_widget = self.query_one("#status", Static)

        status_map = {
            Status.IDLE: ("", "status-idle"),
            Status.RUNNING: ("running", "status-running"),
            Status.PAUSED: ("paused", "status-paused"),
            Status.COMPLETE: ("complete", "status-complete"),
            Status.ERROR: ("error", "status-error"),
        }

        label, css_class = status_map[self.status]
        status_widget.update(label)

        status_widget.remove_class(
            "status-idle", "status-running", "status-paused", "status-complete", "status-error"
        )
        status_widget.add_class(css_class)
