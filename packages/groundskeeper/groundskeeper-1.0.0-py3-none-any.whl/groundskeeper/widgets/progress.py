"""Progress bar widget with Groundskeeper's digging animation."""

from textual.app import ComposeResult
from textual.reactive import reactive
from textual.timer import Timer
from textual.widget import Widget
from textual.widgets import Static

from groundskeeper.constants import PROGRESS_ANIMATION_INTERVAL, PROGRESS_BAR_WIDTH

# Groundskeeper's digging animation frames (ASCII pickaxe motion)
GROUNDSKEEPER_DIG_FRAMES = ["⛏", "⚒", "🔨", "⛏"]  # Digging tools
GROUNDSKEEPER_DIG_ASCII = ["\\", "|", "/", "-"]  # Fallback ASCII animation


class Progress(Widget):
    """Progress indicator with animated digger while work is in progress."""

    DEFAULT_CSS = """
    Progress {
        height: 1;
        layout: horizontal;
        padding: 0;
        margin: 0;
    }

    Progress .label {
        width: auto;
        color: $text-muted;
        margin-right: 1;
    }

    Progress .bar {
        width: auto;
        transition: color 300ms;
    }

    Progress .stats {
        width: auto;
        color: $text-muted;
        margin-left: 1;
    }
    """

    completed: reactive[int] = reactive(0)
    total: reactive[int] = reactive(0)
    is_active: reactive[bool] = reactive(False)

    _animation_timer: Timer | None = None
    _frame_index: int = 0

    def compose(self) -> ComposeResult:
        yield Static("stories", classes="label")
        yield Static("", id="bar", classes="bar")
        yield Static("", id="stats", classes="stats")

    def on_mount(self) -> None:
        # Start animation timer (runs continuously, animation only shows when active)
        self._animation_timer = self.set_interval(
            PROGRESS_ANIMATION_INTERVAL, self._animate_progress
        )

    def on_unmount(self) -> None:
        if self._animation_timer:
            self._animation_timer.stop()

    def _animate_progress(self) -> None:
        """Advance animation frame and refresh if active."""
        if self.is_active and self.completed < self.total:
            self._frame_index = (self._frame_index + 1) % len(GROUNDSKEEPER_DIG_ASCII)
            self._update()

    def watch_completed(self) -> None:
        self._update()

    def watch_total(self) -> None:
        self._update()

    def watch_is_active(self) -> None:
        self._update()

    def _update(self) -> None:
        if not self.is_mounted:
            return

        bar_widget = self.query_one("#bar", Static)
        stats_widget = self.query_one("#stats", Static)

        if self.total == 0:
            bar_widget.update("[dim]───────────────────────[/]")
            stats_widget.update("")
            return

        # Calculate progress
        pct = self.completed / self.total
        width = PROGRESS_BAR_WIDTH
        filled = int(pct * width)
        remaining = width - filled

        if self.completed >= self.total:
            # Complete - full green bar
            bar = f"[$success]{'━' * width}[/]"
        elif self.is_active and remaining > 0:
            # In progress with animation
            digger = GROUNDSKEEPER_DIG_ASCII[self._frame_index]
            if filled > 0:
                bar = f"[$primary]{'━' * filled}[/][bold $warning]{digger}[/][dim]{'─' * (remaining - 1)}[/]"
            else:
                bar = f"[bold $warning]{digger}[/][dim]{'─' * (remaining - 1)}[/]"
        elif filled > 0:
            # Has progress but not active
            bar = f"[$primary]{'━' * filled}[/][dim]{'─' * remaining}[/]"
        else:
            # Empty
            bar = f"[dim]{'─' * width}[/]"

        bar_widget.update(bar)
        stats_widget.update(f"{self.completed}/{self.total}")
