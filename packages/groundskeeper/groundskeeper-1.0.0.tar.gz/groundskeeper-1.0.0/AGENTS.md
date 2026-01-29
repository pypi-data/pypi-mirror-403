# Agent Guidelines for Groundskeeper

This document provides essential information for AI coding agents working on the **Groundskeeper** project.

## Project Overview

Groundskeeper is a minimal TUI (Text User Interface) for autonomous agent loops, built with Python 3.12+ and [Textual](https://textual.textualize.io/). It monitors AI-powered development workflows using various CLI agent backends (claude, opencode, kiro, gemini, codex, amp, copilot).

**Philosophy:** Less is more. Show only what matters, hide noise, stay out of the way.

## Build & Development Commands

### Setup
```bash
# Install dependencies (recommended)
uv sync

# Install in editable mode
pip install -e .
```

### Linting & Formatting
```bash
# Lint code
uv run poe lint          # or: ruff check src/

# Format code
uv run poe format        # or: ruff format src/

# Check formatting without changes
uv run poe format-check  # or: ruff format --check src/
```

### Type Checking
```bash
uv run poe typecheck     # or: pyrefly check
```

### Testing
```bash
# Run all tests
uv run poe test          # or: pytest tests/ -v --tb=short

# Run tests with coverage
uv run poe test-cov      # or: pytest tests/ -v --cov=src/groundskeeper --cov-report=term-missing

# Run a single test file
pytest tests/test_app.py -v

# Run a single test class
pytest tests/test_app.py::TestAppLifecycle -v

# Run a single test function
pytest tests/test_app.py::TestAppLifecycle::test_app_starts_in_idle_state -v

# Run with specific markers (if defined)
pytest tests/ -v -m "not slow"
```

### Combined Checks
```bash
# Run all checks (format, lint, typecheck, test)
uv run poe check
```

### Pre-commit Hooks
```bash
# Pre-commit runs automatically on git commit
# Hooks: ruff-check, ruff-format, pyrefly
```

### Running the Application
```bash
# Using entry point
groundskeeper --spec my-feature

# Or via python module
python -m groundskeeper --spec my-feature
```

## Code Style & Standards

### Import Organization
- **Standard library imports** first
- **Third-party imports** second (textual, watchfiles, etc.)
- **Local imports** last (groundskeeper modules)
- Use absolute imports: `from groundskeeper.parser import parse_prd`
- Group imports with blank lines between categories
- Sort alphabetically within groups (handled by ruff/isort)

Example:
```python
import asyncio
import json
from pathlib import Path

from textual.app import App
from textual.reactive import reactive

from groundskeeper.parser import parse_prd
from groundskeeper.state import State, Status
```

### Formatting
- **Line length:** 100 characters (configured in ruff)
- **Quote style:** Double quotes (`"`)
- **Indentation:** 4 spaces (no tabs)
- **Trailing commas:** Used in multi-line structures
- Ruff handles all formatting automatically

### Type Hints
- **Python 3.12+ syntax:** Use PEP 695 type aliases where appropriate
  ```python
  type BackendType = Literal["claude", "opencode", "kiro", ...]
  ```
- Use `|` for unions: `Path | None` (not `Optional[Path]`)
- Use `list[str]`, `dict[str, int]` (not `List`, `Dict`)
- Type all function parameters and return values
- Use `collections.abc` types for protocols: `Callable`, `AsyncIterator`
- Avoid bare `except:` - specify exception types

### Naming Conventions
- **Classes:** PascalCase (`GroundskeeperApp`, `SpecManager`)
- **Functions/methods:** snake_case (`run_iteration`, `parse_prd`)
- **Constants:** UPPER_SNAKE_CASE (`MAX_OUTPUT_LINES`, `ANSI_ESCAPE_PATTERN`)
- **Private attributes:** Leading underscore (`_gk_dir`, `_spec_manager`)
- **Type aliases:** PascalCase or snake_case depending on usage

### Async/Await Patterns
- Use `async def` for coroutines
- Prefer `asyncio.create_task()` for fire-and-forget tasks (RUF006 ignored)
- Always handle `asyncio.CancelledError` in long-running tasks
- Use `await` for I/O operations
- Clean up tasks in `finally` blocks

Example:
```python
try:
    async for event in agent.run(prompt):
        # Process event
        pass
except asyncio.CancelledError:
    await agent.stop()
    raise
finally:
    await agent.stop()
```

### Error Handling
- Catch specific exceptions: `json.JSONDecodeError`, `OSError`, `ValueError`
- Use `try/except/finally` for resource cleanup
- Log errors appropriately (use `on_output` callback in runner)
- Return error status codes from iteration functions

### Docstrings
- Use for public classes, methods, and complex functions
- Follow Google style (short description, Args, Returns, Yields)
- Keep focused on "why" and behavior, not implementation details

Example:
```python
def create_agent(
    backend: BackendType,
    workspace: Path,
    allow_file_creation: bool = False,
) -> AgentProtocol:
    """Create an agent for the specified backend.

    Args:
        backend: Backend type to use ("claude", "opencode", etc.)
        workspace: Working directory for the agent
        allow_file_creation: For Claude, whether to allow file creation mode

    Returns:
        Configured agent instance
    """
```

## Architecture Patterns

### Textual Patterns
- **Reactive attributes:** Use `reactive[Type]` for UI state
- **Bindings:** Define as class-level `BINDINGS` list
- **CSS:** Keep in `groundskeeper.tcss`, reference via `CSS_PATH`
- **Screens:** Modal dialogs pushed with `push_screen()`
- **Messages:** Custom messages for widget communication

### Agent Protocol
- All agents implement `AgentProtocol` abstract base class
- Emit events: `TextEvent`, `FileEvent`, `ErrorEvent`, `CompleteEvent`
- Use `async for` to consume agent output streams
- Always call `await agent.stop()` in cleanup

### State Management
- Centralized in `State` dataclass (src/groundskeeper/state.py:1)
- Status enum: `IDLE`, `RUNNING`, `PAUSED`, `ERROR`, `COMPLETE`
- Reactive updates trigger UI refreshes automatically

### File Watching
- `watchfiles` library for monitoring prd.json and progress.txt
- Async task with `stop_event` for graceful shutdown
- Callbacks: `on_prd_change()`, `on_progress_change()`

### Settings System
- Schema-driven with dot-notation keys: `settings.get("ui.theme", str)`
- Type coercion via `expect_type` parameter
- Reactive callbacks via `on_set_callback` for CSS class toggling
- Schema in `settings_schema.py`, logic in `settings.py`

Example:
```python
from groundskeeper.settings import Schema, Settings
from groundskeeper.settings_schema import SCHEMA

schema = Schema(SCHEMA)
settings = Settings(schema, {}, on_set_callback=self.on_setting)
theme = settings.get("ui.theme", str)  # Returns default or stored value
```

### Messages
- Dataclass-based Textual messages in `messages.py`
- Use `slots=True` for memory efficiency
- Available: `AgentStarted`, `AgentPaused`, `AgentResumed`, `AgentCompleted`, `AgentError`, `OutputAppended`, `StoryUpdated`, `SpecLoaded`, `FileCreated`

### Terminal Themes
- Themes in `themes.py` using `rich.terminal_theme.TerminalTheme`
- Available: dracula, nord, gruvbox-dark, tokyo-night, catppuccin-mocha, solarized-dark
- Access via `get_theme(name)` or `THEMES` dict

### Agent Configuration
- TOML-based configs in `data/agents/*.toml`
- Load via `load_agent_config(name)` from `agent_config.py`
- List available via `list_available_agents()`
- TypedDict-based: `AgentConfig`, `AgentMetadata`, `AgentArguments`

## Project Structure

```
groundskeeper/
├── src/groundskeeper/
│   ├── __main__.py          # CLI entry point
│   ├── app.py               # Main GroundskeeperApp (Textual app)
│   ├── runner.py            # AI agent execution loop
│   ├── parser.py            # PRD/progress parsing
│   ├── specmanager.py       # Spec CRUD operations
│   ├── state.py             # Application state dataclasses
│   ├── watcher.py           # File watching
│   ├── prompts.py           # Agent prompts
│   ├── ansi.py              # ANSI escape code handling
│   ├── version_check.py     # Update checking
│   ├── groundskeeper.tcss   # Textual CSS styling
│   ├── settings.py          # Schema-driven settings system
│   ├── settings_schema.py   # Settings schema definition
│   ├── messages.py          # Custom Textual messages
│   ├── themes.py            # Terminal theme definitions
│   ├── agent_config.py      # TOML agent config loader
│   ├── _loop.py             # Utility for key parsing
│   ├── agents/
│   │   ├── protocol.py      # AgentProtocol interface
│   │   ├── claude.py        # Claude CLI agent
│   │   └── generic.py       # Generic agent adapter
│   ├── data/
│   │   ├── __init__.py      # Data directory exports
│   │   └── agents/          # TOML backend configs (claude.toml, etc.)
│   ├── screens/             # Modal screens (help, specs, etc.)
│   └── widgets/             # Custom Textual widgets
├── tests/
│   ├── conftest.py          # Pytest fixtures
│   └── test_app.py          # App behavior tests
├── pyproject.toml           # Build config, dependencies, tool settings
├── .pre-commit-config.yaml  # Pre-commit hooks
└── design.md                # Design philosophy & architecture
```

## Common Pitfalls

1. **Ruff RUF012:** Don't use mutable defaults in ClassVar. Textual `BINDINGS` are explicitly designed this way (ignored).
2. **Ruff RUF006:** Fire-and-forget `asyncio.create_task()` is intentional for background tasks (ignored).
3. **Always await agent.stop():** Ensure cleanup in exception handlers.
4. **Test with pilot.pause():** Textual tests need `await pilot.pause()` for UI updates.
5. **Path handling:** Use `Path` objects consistently, not string paths.

## Testing Guidelines

- Use `pytest` with `pytest-asyncio` for async tests
- Use `pytest-textual-snapshot` for TUI snapshot testing
- Fixtures in `conftest.py` provide `app_no_spec` and `app_with_spec`
- Use `async with app.run_test() as pilot:` pattern
- Test user-facing interactions: keybindings, state transitions, screen navigation
- Mock external dependencies (file I/O, subprocesses)
