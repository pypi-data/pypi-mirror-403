"""Tests for user-facing TUI features.

Focus on critical user interactions:
- App startup behavior
- Keyboard navigation
- State transitions (pause/resume/quit)
- Screen navigation
"""

from pathlib import Path

import pytest

from groundskeeper.app import GroundskeeperApp
from groundskeeper.screens import (
    ArchiveScreen,
    ClearHistoryConfirmScreen,
    EditSpecScreen,
    HelpScreen,
    HistoryScreen,
    LogsScreen,
    NewSpecScreen,
    QuitConfirmScreen,
    SpecsScreen,
)
from groundskeeper.state import Status

from .conftest import create_test_prd


class TestAppLifecycle:
    """Test app startup and basic state management."""

    async def test_app_starts_in_idle_state(self, app_no_spec: GroundskeeperApp):
        """App should start in IDLE state without a spec."""
        async with app_no_spec.run_test() as pilot:  # noqa: F841
            assert app_no_spec.state.status == Status.IDLE
            assert app_no_spec.state.stories == []

    async def test_app_loads_spec_on_mount(self, app_with_spec: GroundskeeperApp):
        """App should load stories from prd.json on mount."""
        async with app_with_spec.run_test() as pilot:
            await pilot.pause()
            assert len(app_with_spec.state.stories) == 1
            assert app_with_spec.state.stories[0].id == "US-001"


class TestKeyboardNavigation:
    """Test that keyboard shortcuts navigate to correct screens."""

    @pytest.mark.parametrize(
        "key,screen_type",
        [
            ("?", HelpScreen),
            ("l", LogsScreen),
            ("h", HistoryScreen),
            ("s", SpecsScreen),
            ("n", NewSpecScreen),
            ("a", ArchiveScreen),
        ],
    )
    async def test_screen_keybindings(
        self, app_no_spec: GroundskeeperApp, key: str, screen_type: type
    ):
        """Keybinding should open the expected screen."""
        async with app_no_spec.run_test() as pilot:
            await pilot.press(key)
            await pilot.pause()
            assert isinstance(app_no_spec.screen, screen_type)


class TestQuitBehavior:
    """Test quit behavior in different states."""

    async def test_quit_when_idle_exits_immediately(self, app_no_spec: GroundskeeperApp):
        """Pressing q when idle should exit without confirmation."""
        async with app_no_spec.run_test() as pilot:
            await pilot.press("q")
            await pilot.pause()
            assert not app_no_spec.is_running

    async def test_quit_when_running_shows_confirmation(self, app_no_spec: GroundskeeperApp):
        """Pressing q when running should show confirmation dialog."""
        async with app_no_spec.run_test() as pilot:
            app_no_spec.state.status = Status.RUNNING
            await pilot.press("q")
            await pilot.pause()
            assert isinstance(app_no_spec.screen, QuitConfirmScreen)

    @pytest.mark.parametrize(
        "key,should_exit",
        [
            ("y", True),
            ("n", False),
            ("escape", False),
        ],
    )
    async def test_quit_confirmation_responses(
        self, app_no_spec: GroundskeeperApp, key: str, should_exit: bool
    ):
        """Test quit confirmation dialog responses."""
        async with app_no_spec.run_test() as pilot:
            app_no_spec.state.status = Status.RUNNING
            await pilot.press("q")
            await pilot.pause()

            await pilot.press(key)
            await pilot.pause()

            if should_exit:
                assert not app_no_spec.is_running
            else:
                assert not isinstance(app_no_spec.screen, QuitConfirmScreen)


class TestPauseResume:
    """Test pause and resume functionality."""

    async def test_pause_when_running(self, app_no_spec: GroundskeeperApp):
        """Pressing p when running should pause."""
        async with app_no_spec.run_test() as pilot:
            app_no_spec.state.status = Status.RUNNING
            await pilot.press("p")
            await pilot.pause()
            assert app_no_spec.state.status == Status.PAUSED

    async def test_pause_when_idle_does_nothing(self, app_no_spec: GroundskeeperApp):
        """Pressing p when idle should not change state."""
        async with app_no_spec.run_test() as pilot:
            assert app_no_spec.state.status == Status.IDLE
            await pilot.press("p")
            await pilot.pause()
            assert app_no_spec.state.status == Status.IDLE

    async def test_resume_when_paused(self, app_no_spec: GroundskeeperApp):
        """Pressing r when paused should resume."""
        async with app_no_spec.run_test() as pilot:
            app_no_spec.state.status = Status.PAUSED
            await pilot.press("r")
            await pilot.pause()
            assert app_no_spec.state.status == Status.RUNNING


class TestStartSession:
    """Test session start behavior."""

    async def test_start_from_idle(self, app_with_spec: GroundskeeperApp):
        """Pressing g when idle should start the session."""
        async with app_with_spec.run_test() as pilot:
            assert app_with_spec.state.status == Status.IDLE
            await pilot.press("g")
            await pilot.pause()
            assert app_with_spec.state.status != Status.IDLE


class TestSpecsScreen:
    """Test specs screen functionality."""

    async def test_empty_specs_shows_message(self, app_no_spec: GroundskeeperApp):
        """Specs screen should show empty message when no specs exist."""
        async with app_no_spec.run_test() as pilot:
            await pilot.press("s")
            await pilot.pause()
            assert isinstance(app_no_spec.screen, SpecsScreen)
            empty = app_no_spec.screen.query(".empty")
            assert len(empty) > 0

    async def test_vim_navigation(self, temp_workspace: Path):
        """Specs screen should support j/k navigation."""
        specs_dir = temp_workspace / ".groundskeeper" / "specs"
        for i in range(3):
            create_test_prd(specs_dir / f"spec-{i}.json")

        app = GroundskeeperApp(
            max_iterations=5,
            groundskeeper_dir=temp_workspace / ".groundskeeper",
        )

        async with app.run_test() as pilot:
            await pilot.press("s")
            await pilot.pause()

            from textual.widgets import OptionList

            option_list = app.screen.query_one("#spec-list", OptionList)
            initial_index = option_list.highlighted

            await pilot.press("j")
            await pilot.pause()
            assert option_list.highlighted == initial_index + 1

            await pilot.press("k")
            await pilot.pause()
            assert option_list.highlighted == initial_index


class TestSpecActions:
    """Test actions that require an active spec."""

    async def test_edit_spec_opens_screen(self, app_with_spec: GroundskeeperApp):
        """Pressing e with active spec should open edit screen."""
        async with app_with_spec.run_test() as pilot:
            await pilot.pause()
            await pilot.press("e")
            await pilot.pause()
            assert isinstance(app_with_spec.screen, EditSpecScreen)

    async def test_edit_without_spec_does_nothing(self, app_no_spec: GroundskeeperApp):
        """Pressing e without active spec should not open edit screen."""
        async with app_no_spec.run_test() as pilot:
            await pilot.press("e")
            await pilot.pause()
            assert not isinstance(app_no_spec.screen, EditSpecScreen)

    async def test_clear_history_shows_confirmation(self, app_with_spec: GroundskeeperApp):
        """Pressing c with active spec should show confirmation."""
        async with app_with_spec.run_test() as pilot:
            await pilot.pause()
            await pilot.press("c")
            await pilot.pause()
            assert isinstance(app_with_spec.screen, ClearHistoryConfirmScreen)

    async def test_clear_history_without_spec_does_nothing(
        self, app_no_spec: GroundskeeperApp
    ):
        """Pressing c without active spec should not show confirmation."""
        async with app_no_spec.run_test() as pilot:
            await pilot.press("c")
            await pilot.pause()
            assert not isinstance(app_no_spec.screen, ClearHistoryConfirmScreen)
