"""Message definitions for widget communication in groundskeeper TUI."""

from dataclasses import dataclass
from pathlib import Path

from textual.message import Message


@dataclass(slots=True)
class AgentStarted(Message):
    """Agent execution has started."""

    backend: str
    iteration: int


@dataclass(slots=True)
class AgentPaused(Message):
    """Agent execution was paused."""

    pass


@dataclass(slots=True)
class AgentResumed(Message):
    """Agent execution resumed."""

    pass


@dataclass(slots=True)
class AgentCompleted(Message):
    """Agent iteration completed."""

    success: bool
    iteration: int


@dataclass(slots=True)
class AgentError(Message):
    """Agent encountered an error."""

    message: str
    recoverable: bool = True


@dataclass(slots=True)
class OutputAppended(Message):
    """New output text to display."""

    text: str
    is_error: bool = False


@dataclass(slots=True)
class StoryUpdated(Message):
    """Story status changed."""

    story_id: str
    passes: bool


@dataclass(slots=True)
class SpecLoaded(Message):
    """A spec was loaded."""

    spec_name: str
    story_count: int


@dataclass(slots=True)
class FileCreated(Message):
    """Agent created a file."""

    path: Path
    content: str | None = None
