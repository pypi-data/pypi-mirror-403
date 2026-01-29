import json
from pathlib import Path

from .state import Story


def parse_prd(path: Path) -> list[Story]:
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text())
        return [
            Story(
                id=s.get("id", ""),
                title=s.get("title", ""),
                description=s.get("description", ""),
                acceptance_criteria=s.get("acceptanceCriteria", []),
                priority=s.get("priority", 0),
                passes=s.get("passes", False),
                notes=s.get("notes", ""),
            )
            for s in data.get("userStories", [])
        ]
    except (json.JSONDecodeError, KeyError):
        return []


def parse_history(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text()
