from __future__ import annotations

from typing import Required, TypedDict


class SchemaDict(TypedDict, total=False):
    """Typing for schema data structure."""

    key: Required[str]
    title: Required[str]
    type: Required[str]
    help: str
    choices: list[str] | list[tuple[str, str]] | None
    default: object
    fields: list[SchemaDict]
    validate: list[dict]
    editable: bool


SCHEMA: list[SchemaDict] = [
    {
        "key": "ui",
        "title": "User Interface",
        "type": "object",
        "fields": [
            {
                "key": "theme",
                "title": "Theme",
                "help": "Color theme for the interface",
                "type": "choices",
                "default": "terminal",
                "choices": [
                    "terminal",
                    "dracula",
                    "nord",
                    "gruvbox-dark",
                    "tokyo-night",
                    "catppuccin-mocha",
                    "solarized-dark",
                ],
            },
            {
                "key": "compact-output",
                "title": "Compact output",
                "help": "Use compact output mode",
                "type": "boolean",
                "default": False,
            },
            {
                "key": "max-output-lines",
                "title": "Maximum output lines",
                "help": "Maximum number of lines to display in output",
                "type": "integer",
                "default": 10000,
                "validate": [{"type": "minimum", "value": 100}],
            },
            {
                "key": "show-quotes",
                "title": "Show quotes",
                "help": "Show inspirational quotes while waiting",
                "type": "boolean",
                "default": True,
            },
        ],
    },
    {
        "key": "agent",
        "title": "Agent Settings",
        "type": "object",
        "fields": [
            {
                "key": "default-backend",
                "title": "Default backend",
                "help": "Default agent backend to use",
                "type": "choices",
                "default": "claude",
                "choices": [
                    "claude",
                    "opencode",
                    "kiro",
                    "gemini",
                    "codex",
                    "amp",
                    "copilot",
                ],
            },
            {
                "key": "max-iterations",
                "title": "Maximum iterations",
                "help": "Maximum number of agent iterations per run",
                "type": "integer",
                "default": 10,
                "validate": [{"type": "minimum", "value": 1}],
            },
            {
                "key": "auto-start",
                "title": "Auto-start agent",
                "help": "Automatically start the agent on launch",
                "type": "boolean",
                "default": False,
            },
        ],
    },
]
