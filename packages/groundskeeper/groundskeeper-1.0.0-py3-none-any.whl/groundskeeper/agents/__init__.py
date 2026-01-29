"""Agent abstraction layer for AI tool integration."""

from .claude import ClaudeAgent
from .generic import BackendConfig, GenericAgent
from .protocol import (
    AgentEvent,
    AgentProtocol,
    CompleteEvent,
    ErrorEvent,
    FileEvent,
    TextEvent,
)

__all__ = [
    "AgentEvent",
    "AgentProtocol",
    "BackendConfig",
    "ClaudeAgent",
    "CompleteEvent",
    "ErrorEvent",
    "FileEvent",
    "GenericAgent",
    "TextEvent",
]
