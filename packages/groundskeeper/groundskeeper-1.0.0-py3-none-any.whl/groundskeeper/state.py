"""State management for groundskeeper TUI."""

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path


class Status(Enum):
    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETE = "complete"
    ERROR = "error"


@dataclass(slots=True)
class Story:
    """A user story from the PRD."""

    id: str
    title: str
    description: str
    acceptance_criteria: list[str]
    priority: int
    passes: bool
    notes: str = ""


@dataclass(slots=True)
class Spec:
    """A PRD specification file."""

    name: str
    path: Path
    project: str
    branch: str
    description: str
    total: int
    passed: int
    is_active: bool = False

    @property
    def status(self) -> str:
        if self.is_active:
            return "active"
        if self.passed == self.total and self.total > 0:
            return "complete"
        return "ready"


@dataclass(slots=True)
class ArchivedSession:
    """An archived session."""

    name: str
    path: Path
    project: str
    description: str
    total: int
    passed: int


@dataclass
class State:
    """Application state."""

    max_iterations: int = 10
    current_iteration: int = 0
    status: Status = Status.IDLE
    stories: list[Story] = field(default_factory=list)
    history: str = ""
    workspace: Path = field(default_factory=Path.cwd)
    groundskeeper_dir: Path = field(default_factory=lambda: Path.cwd() / ".groundskeeper")
    specs: list[Spec] = field(default_factory=list)
    active_spec: Spec | None = None

    @property
    def current_story(self) -> Story | None:
        pending = [s for s in self.stories if not s.passes]
        return min(pending, key=lambda s: s.priority) if pending else None

    @property
    def completed_count(self) -> int:
        return sum(1 for s in self.stories if s.passes)

    @property
    def total_count(self) -> int:
        return len(self.stories)

    @property
    def spec_name(self) -> str:
        return self.active_spec.name if self.active_spec else ""
