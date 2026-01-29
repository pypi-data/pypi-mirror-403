import json
import shutil
from datetime import datetime
from pathlib import Path

from .constants import PROGRESS_INITIAL
from .state import ArchivedSession, Spec


class SpecManager:
    """Manage PRD specs in .groundskeeper directory."""

    def __init__(self, base_dir: Path | None = None):
        self.base = base_dir or Path.cwd() / ".groundskeeper"
        self.specs_dir = self.base / "specs"
        self.active_dir = self.base / "active"
        self.archive_dir = self.base / "archive"

    def ensure_structure(self) -> None:
        """Create directory structure if missing."""
        self.specs_dir.mkdir(parents=True, exist_ok=True)
        self.active_dir.mkdir(parents=True, exist_ok=True)
        self.archive_dir.mkdir(parents=True, exist_ok=True)

    def list_specs(self) -> list[Spec]:
        """List all available specs from specs directory."""
        specs: list[Spec] = []
        active_name = self._get_active_name()

        if not self.specs_dir.exists():
            return specs

        for path in sorted(self.specs_dir.glob("*.json")):
            spec = self._load_spec(path)
            if spec:
                spec.is_active = spec.name == active_name
                specs.append(spec)

        return specs

    def get_active(self) -> Spec | None:
        """Get currently active spec."""
        prd_path = self.active_dir / "prd.json"
        if not prd_path.exists():
            return None
        spec = self._load_spec(prd_path)
        if spec:
            spec.is_active = True
        return spec

    def get_active_prd_path(self) -> Path:
        """Get path to active prd.json."""
        return self.active_dir / "prd.json"

    def get_active_progress_path(self) -> Path:
        """Get path to active progress.txt."""
        return self.active_dir / "progress.txt"

    def activate(self, spec: Spec) -> None:
        """Copy spec to active directory."""
        self.ensure_structure()

        # Archive current active if different
        current = self.get_active()
        if current and current.name != spec.name:
            self.archive_active()

        # Copy spec to active
        dest = self.active_dir / "prd.json"
        shutil.copy(spec.path, dest)

        # Create empty progress.txt if not exists
        progress = self.active_dir / "progress.txt"
        if not progress.exists():
            progress.write_text(PROGRESS_INITIAL)

    def archive_active(self) -> None:
        """Move active spec to archive with timestamp."""
        prd_path = self.active_dir / "prd.json"
        progress_path = self.active_dir / "progress.txt"

        if not prd_path.exists():
            return

        spec = self._load_spec(prd_path)
        if not spec:
            return

        # Create archive folder
        timestamp = datetime.now().strftime("%Y-%m-%d")
        archive_name = f"{timestamp}-{spec.name}"
        archive_folder = self.archive_dir / archive_name

        # Handle duplicate names
        counter = 1
        while archive_folder.exists():
            archive_folder = self.archive_dir / f"{archive_name}-{counter}"
            counter += 1

        archive_folder.mkdir(parents=True, exist_ok=True)

        # Move files
        shutil.move(str(prd_path), str(archive_folder / "prd.json"))
        if progress_path.exists():
            shutil.move(str(progress_path), str(archive_folder / "progress.txt"))

    def create_spec(self, name: str, prd_data: dict[str, object]) -> Spec:
        """Save new spec to specs directory."""
        self.ensure_structure()

        # Sanitize name
        safe_name = name.lower().replace(" ", "-").replace("_", "-")
        path = self.specs_dir / f"{safe_name}.json"

        # Handle duplicates
        counter = 1
        while path.exists():
            path = self.specs_dir / f"{safe_name}-{counter}.json"
            counter += 1

        path.write_text(json.dumps(prd_data, indent=2))

        spec = self._load_spec(path)
        if not spec:
            raise ValueError("Failed to create spec")
        return spec

    def delete_spec(self, spec: Spec) -> None:
        """Remove spec file."""
        if spec.path.exists():
            spec.path.unlink()

    def update_spec(self, path: Path, prd_data: dict) -> Spec:
        """Update an existing spec file."""
        path.write_text(json.dumps(prd_data, indent=2))
        spec = self._load_spec(path)
        if not spec:
            raise ValueError("Failed to update spec")
        return spec

    def validate_spec_json(self, json_str: str) -> tuple[bool, str, dict | None]:
        """Validate spec JSON.

        Returns:
            Tuple of (is_valid, error_message, parsed_dict)
        """
        try:
            parsed = json.loads(json_str)
        except json.JSONDecodeError as e:
            return False, f"JSON syntax error: {e.msg} (line {e.lineno})", None

        # Check required fields
        required_fields = ["project", "userStories"]
        missing = [f for f in required_fields if f not in parsed]
        if missing:
            return False, f"Missing required fields: {', '.join(missing)}", None

        # Validate userStories structure
        stories = parsed.get("userStories", [])
        if not isinstance(stories, list):
            return False, "userStories must be an array", None

        for i, story in enumerate(stories):
            if not isinstance(story, dict):
                return False, f"Story {i + 1} must be an object", None
            if "id" not in story:
                return False, f"Story {i + 1} missing 'id' field", None
            if "title" not in story:
                return False, f"Story {i + 1} missing 'title' field", None

        return True, "Valid spec JSON", parsed

    def clear_history(self) -> None:
        """Clear the active progress.txt file, resetting to initial state."""
        progress_path = self.get_active_progress_path()
        progress_path.write_text(PROGRESS_INITIAL)

    def list_archives(self) -> list[ArchivedSession]:
        """List all archived sessions."""
        archives: list[ArchivedSession] = []

        if not self.archive_dir.exists():
            return archives

        for path in sorted(self.archive_dir.iterdir(), reverse=True):
            if path.is_dir():
                prd_path = path / "prd.json"
                if prd_path.exists():
                    spec = self._load_spec(prd_path)
                    if spec:
                        archives.append(
                            ArchivedSession(
                                name=path.name,
                                path=path,
                                project=spec.project,
                                description=spec.description,
                                total=spec.total,
                                passed=spec.passed,
                            )
                        )

        return archives

    def delete_archive(self, archive: ArchivedSession) -> None:
        """Delete an archived session folder."""
        if archive.path.exists() and archive.path.is_dir():
            shutil.rmtree(archive.path)

    def _load_spec(self, path: Path) -> Spec | None:
        """Load a spec from a JSON file."""
        if not path.exists():
            return None

        try:
            data = json.loads(path.read_text())
            stories = data.get("userStories", [])
            passed = sum(1 for s in stories if s.get("passes", False))

            return Spec(
                name=path.stem,
                path=path,
                project=data.get("project", ""),
                branch=data.get("branchName", ""),
                description=data.get("description", ""),
                total=len(stories),
                passed=passed,
            )
        except (json.JSONDecodeError, KeyError):
            return None

    def _get_active_name(self) -> str:
        """Get name of currently active spec."""
        active = self.get_active()
        return active.name if active else ""
