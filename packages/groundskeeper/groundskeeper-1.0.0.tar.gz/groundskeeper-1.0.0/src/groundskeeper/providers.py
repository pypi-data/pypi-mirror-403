"""Command palette provider for Groundskeeper."""

from functools import partial
from typing import TYPE_CHECKING

from textual.command import DiscoveryHit, Hit, Hits, Provider

if TYPE_CHECKING:
    from groundskeeper.app import GroundskeeperApp


class GroundskeeperProvider(Provider):
    """Command provider for Groundskeeper app actions."""

    @property
    def _app(self) -> "GroundskeeperApp":
        return self.app  # type: ignore[return-value]

    async def discover(self) -> Hits:
        """Discover all available commands."""
        app = self._app
        commands = [
            ("Start Session", app.action_start, "Start the agent loop (g)"),
            ("Pause Session", app.action_pause, "Pause running agent (p)"),
            ("Resume Session", app.action_resume, "Resume paused agent (r)"),
            ("Browse Specs", app.action_specs, "Browse and select specs (s)"),
            ("New Spec", app.action_new_spec, "Create new spec (n)"),
            ("Edit Spec", app.action_edit_spec, "Edit active spec (e)"),
            ("View Archives", app.action_archives, "View archived sessions (a)"),
            ("View Logs", app.action_logs, "View session logs (l)"),
            ("View History", app.action_history, "View iteration history (h)"),
            ("Archive Session", app.action_archive_session, "Archive current session (x)"),
            ("Clear History", app.action_clear_history, "Clear session history (c)"),
            ("Settings", app.action_settings, "Open settings (,)"),
            ("Help", app.action_help, "Show help (?)"),
            ("Quit", app.action_quit_app, "Quit application (q)"),
        ]
        for name, callback, help_text in commands:
            yield DiscoveryHit(name, partial(self._run_action, callback), help=help_text)

    async def search(self, query: str) -> Hits:
        """Search for commands matching query."""
        matcher = self.matcher(query)
        async for hit in self.discover():
            score = matcher.match(hit.match_display)
            if score > 0:
                yield Hit(
                    score,
                    matcher.highlight(hit.match_display),
                    hit.command,
                    help=hit.help,
                )

    def _run_action(self, callback: object) -> None:
        """Run an action callback."""
        if callable(callback):
            callback()
