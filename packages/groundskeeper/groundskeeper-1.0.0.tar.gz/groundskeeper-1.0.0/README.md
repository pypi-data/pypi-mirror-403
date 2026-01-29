# Groundskeeper

Minimal TUI for autonomous agent loops. Built with Python 3.12+ and Textual.

> Less is more. Show only what matters, hide noise, stay out of the way.

## Install

```bash
uv sync
# or
pip install -e .
```

## Usage

```bash
groundskeeper --spec my-feature
```

## Development

```bash
uv run poe lint        # ruff check
uv run poe format      # ruff format
uv run poe typecheck   # pyrefly check
uv run poe test        # pytest
uv run poe check       # all checks
```

## Philosophy

- **Density over sprawl:** One screen, no scrolling
- **Calm aesthetics:** Muted colors, clean lines
- **Keyboard-first:** Every action is a single keypress
- **Progressive disclosure:** Details shown on demand

## Architecture

Monitors AI-powered development workflows using various CLI agent backends (claude, opencode, kiro, gemini, codex, amp, copilot).

See `AGENTS.md` for coding guidelines and `design.md` for architecture.