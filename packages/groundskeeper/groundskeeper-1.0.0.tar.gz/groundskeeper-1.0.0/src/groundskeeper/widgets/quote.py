"""Groundskeeper quote widget with typing animation effect."""

import random

from textual.reactive import reactive
from textual.timer import Timer
from textual.widgets import Static

# Groundskeeper Groundskeeper's iconic quotes adapted for the app
GROUNDSKEEPER_QUOTES = [
    "Back to work, ya lazy specs!",
    "Ach! There's specs to be done!",
    "Groundskeeper hears ya. Groundskeeper don't care.",
    "Grease me up, woman!",
    "It won't last. Nothing does.",
    "That's the last time ye slap yer Groundskeeper around!",
    "Don't touch Groundskeeper. Good advice!",
    "I'm not a man. I'm a machine!",
    "Ya used me, Skinner! YA USED ME!",
    "Groundskeeper's got the strength of ten men!",
]


class GroundskeeperQuote(Static):
    """Displays rotating Groundskeeper quotes with a typing animation effect.

    The quote types out character by character, then pauses before
    showing the next quote.
    """

    DEFAULT_CSS = """
    GroundskeeperQuote {
        width: auto;
        height: 1;
        color: $text-muted;
    }
    """

    text = reactive("")
    _typing_timer: Timer | None = None
    _pause_timer: Timer | None = None

    def __init__(
        self,
        *,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
    ) -> None:
        super().__init__(name=name, id=id, classes=classes)
        self._full_text = ""
        self._char_index = 0

    def on_mount(self) -> None:
        self._start_new_quote()

    def on_unmount(self) -> None:
        self._stop_timers()

    def _stop_timers(self) -> None:
        """Stop all running timers."""
        if self._typing_timer:
            self._typing_timer.stop()
            self._typing_timer = None
        if self._pause_timer:
            self._pause_timer.stop()
            self._pause_timer = None

    def _start_new_quote(self) -> None:
        """Start typing a new random quote."""
        self._stop_timers()
        self._full_text = random.choice(GROUNDSKEEPER_QUOTES)
        self._char_index = 0
        self.text = ""
        # Type at ~20 chars/second for a natural feel
        self._typing_timer = self.set_interval(0.05, self._type_next_char)

    def _type_next_char(self) -> None:
        """Type the next character in the quote."""
        if self._char_index < len(self._full_text):
            self._char_index += 1
            self.text = self._full_text[: self._char_index]
        else:
            # Done typing - pause before next quote
            self._stop_timers()
            # Wait 5 seconds before showing next quote
            self._pause_timer = self.set_timer(5.0, self._start_new_quote)

    def render(self) -> str:
        # Show cursor while typing
        cursor = "▌" if self._char_index < len(self._full_text) else ""
        return f'[italic]"{self.text}{cursor}"[/]'

    def new_quote(self) -> None:
        """Manually trigger a new quote."""
        self._start_new_quote()
