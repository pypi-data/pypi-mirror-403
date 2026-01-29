"""Shared fixtures for Groundskeeper tests."""

import json
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from groundskeeper.app import GroundskeeperApp


def create_test_prd(path: Path, stories: list[dict] | None = None) -> None:
    """Create a test prd.json file."""
    if stories is None:
        stories = [
            {
                "id": "US-001",
                "title": "Test Story",
                "description": "A test story",
                "acceptanceCriteria": ["Criterion 1", "Criterion 2"],
                "priority": 1,
                "passes": False,
            }
        ]
    data = {
        "project": "test-project",
        "branchName": "feature/test",
        "description": "Test PRD",
        "userStories": stories,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2))


@pytest.fixture
def temp_workspace():
    """Create a temporary workspace with .groundskeeper structure."""
    with TemporaryDirectory() as tmpdir:
        workspace = Path(tmpdir)
        gk_dir = workspace / ".groundskeeper"
        gk_dir.mkdir()
        (gk_dir / "specs").mkdir()
        (gk_dir / "active").mkdir()
        (gk_dir / "archive").mkdir()
        yield workspace


@pytest.fixture
def app_with_spec(temp_workspace: Path):
    """Create an app with an active spec loaded."""
    prd_path = temp_workspace / ".groundskeeper" / "active" / "prd.json"
    create_test_prd(prd_path)

    return GroundskeeperApp(
        max_iterations=5,
        prd_path=prd_path,
        groundskeeper_dir=temp_workspace / ".groundskeeper",
    )


@pytest.fixture
def app_no_spec(temp_workspace: Path):
    """Create an app with no active spec."""
    return GroundskeeperApp(
        max_iterations=5,
        groundskeeper_dir=temp_workspace / ".groundskeeper",
    )
