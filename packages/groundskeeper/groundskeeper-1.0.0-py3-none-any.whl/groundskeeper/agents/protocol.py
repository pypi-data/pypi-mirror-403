"""Agent protocol - abstract interface for AI tool integration.

This module defines the contract that all AI agents must implement.
Each agent (Claude, Codex, Gemini, OpenCode, etc.) provides an adapter
that translates its specific output format into common events.
"""

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from dataclasses import dataclass
from pathlib import Path


# Event types emitted by agents
@dataclass
class AgentEvent:
    """Base class for all agent events."""

    pass


@dataclass
class TextEvent(AgentEvent):
    """Streaming text output from the agent."""

    text: str


@dataclass
class FileEvent(AgentEvent):
    """Agent created or modified a file."""

    path: Path
    content: str | None = None  # Content if available, for agents that output but don't write


@dataclass
class ErrorEvent(AgentEvent):
    """An error occurred during agent execution."""

    message: str
    recoverable: bool = False


@dataclass
class CompleteEvent(AgentEvent):
    """Agent has finished execution."""

    success: bool = True
    output: str = ""  # Full accumulated output


class AgentProtocol(ABC):
    """Abstract base class for AI agent integrations.

    Each AI tool (Claude, Codex, Gemini, etc.) should implement this protocol.
    The protocol provides a unified streaming interface that emits events
    as the agent works.

    Example usage:
        agent = ClaudeAgent(workspace=Path.cwd())
        async for event in agent.run("Create a hello world function"):
            match event:
                case TextEvent(text=t):
                    print(t, end="", flush=True)
                case FileEvent(path=p):
                    print(f"Created: {p}")
                case CompleteEvent(success=s):
                    print("Done!" if s else "Failed")
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable name of this agent (e.g., 'Claude', 'Codex')."""
        ...

    @property
    def supports_streaming(self) -> bool:
        """Whether this agent supports real-time output streaming."""
        return True

    @property
    def supports_file_creation(self) -> bool:
        """Whether this agent can create files directly."""
        return True

    @abstractmethod
    def run(self, prompt: str) -> AsyncIterator[AgentEvent]:
        """Execute a prompt and stream events.

        Args:
            prompt: The instruction/prompt for the agent

        Yields:
            AgentEvent instances as the agent works
        """
        ...

    @abstractmethod
    async def stop(self) -> None:
        """Stop the currently running agent process."""
        ...
