"""New spec creation screen with AI agent integration."""

import asyncio
import json
import re
from pathlib import Path

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from textual.reactive import reactive
from textual.screen import ModalScreen
from textual.widgets import RichLog, Static, TextArea

from groundskeeper.agents import ClaudeAgent, CompleteEvent, ErrorEvent, TextEvent


class NewSpecScreen(ModalScreen[Path | None]):
    """Interactive spec creation with AI agent."""

    BINDINGS = [
        Binding("ctrl+s", "submit", "Submit", show=True),
        Binding("ctrl+r", "regenerate", "Regenerate", show=False),
        Binding("escape", "cancel", "Cancel", priority=True),
    ]

    DEFAULT_CSS = """
    NewSpecScreen { align: center middle; }
    NewSpecScreen > Vertical {
        width: 80%;
        height: 80%;
        background: $surface;
        border: round $primary 50%;
        padding: 1;
    }
    NewSpecScreen .title {
        dock: top;
        height: 1;
        color: $primary;
        text-style: bold;
    }
    NewSpecScreen .subtitle {
        color: $text-muted;
        height: 1;
    }
    NewSpecScreen TextArea {
        height: 6;
        background: $background;
        border: round $border 30%;
        margin: 1 0;
    }
    NewSpecScreen TextArea:focus {
        border: round $primary 60%;
    }
    NewSpecScreen TextArea#review-editor {
        height: 1fr;
    }
    NewSpecScreen RichLog {
        height: 1fr;
        background: $background;
        border: round $border 30%;
    }
    NewSpecScreen .hint {
        dock: bottom;
        height: 1;
        color: $text-muted;
    }
    NewSpecScreen .phase-thinking {
        color: $primary;
    }
    NewSpecScreen .phase-complete {
        color: $success;
    }
    NewSpecScreen .phase-error {
        color: $error;
    }
    NewSpecScreen .status {
        height: 1;
        color: $text-muted;
        margin-top: 1;
    }
    NewSpecScreen .status.-valid {
        color: $success;
    }
    NewSpecScreen .status.-invalid {
        color: $error;
    }
    """

    phase: reactive[str] = reactive("input")  # input, thinking, review, complete, error
    validation_status: reactive[str] = reactive("")
    is_valid: reactive[bool] = reactive(True)

    def __init__(self, groundskeeper_dir: Path | None = None) -> None:
        super().__init__()
        self._gk_dir = groundskeeper_dir or Path.cwd() / ".groundskeeper"
        self._created_path: Path | None = None
        self._agent_task: asyncio.Task | None = None
        self._agent: ClaudeAgent | None = None
        self._last_description: str = ""
        self._extracted_json: dict | None = None
        self._spec_path: Path | None = None

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Static("─ new spec ─", classes="title")
            yield Static("Describe your feature:", classes="subtitle", id="subtitle")
            yield TextArea(id="input", tab_behavior="indent")
            yield RichLog(id="output", highlight=True, markup=True)
            yield TextArea(id="review-editor", language="json", theme="monokai", classes="-hidden")
            yield Static("", classes="status -hidden", id="status")
            yield Static("ctrl+s submit · esc cancel", classes="hint", id="hint")

    def on_mount(self) -> None:
        self.query_one("#input", TextArea).focus()

    def watch_phase(self) -> None:
        hint = self.query_one("#hint", Static)
        subtitle = self.query_one("#subtitle", Static)
        input_area = self.query_one("#input", TextArea)
        output_log = self.query_one("#output", RichLog)
        review_editor = self.query_one("#review-editor", TextArea)
        status = self.query_one("#status", Static)

        if self.phase == "input":
            hint.update("ctrl+s submit · esc cancel")
            subtitle.update("Describe your feature:")
            input_area.remove_class("-hidden")
            output_log.add_class("-hidden")
            review_editor.add_class("-hidden")
            status.add_class("-hidden")
        elif self.phase == "thinking":
            hint.update("Agent is working... esc cancel")
            subtitle.update("Generating spec...")
            input_area.add_class("-hidden")
            output_log.remove_class("-hidden")
            review_editor.add_class("-hidden")
            status.add_class("-hidden")
        elif self.phase == "review":
            hint.update("ctrl+s save · ctrl+r regenerate · esc cancel")
            subtitle.update("Review and edit the generated spec:")
            input_area.add_class("-hidden")
            output_log.add_class("-hidden")
            review_editor.remove_class("-hidden")
            status.remove_class("-hidden")
            review_editor.focus()
        elif self.phase == "complete":
            hint.update("a activate · s view specs · esc close")
            subtitle.update("Spec created successfully!")
        elif self.phase == "error":
            hint.update("ctrl+r retry · esc close")
            subtitle.update("Error occurred:")

    def watch_validation_status(self) -> None:
        status_widget = self.query_one("#status", Static)
        status_widget.update(self.validation_status)
        status_widget.remove_class("-valid", "-invalid")
        if self.validation_status:
            status_widget.add_class("-valid" if self.is_valid else "-invalid")

    def action_submit(self) -> None:
        if self.phase == "input":
            description = self.query_one("#input", TextArea).text.strip()
            if description:
                self._last_description = description
                self._start_agent(description)
        elif self.phase == "review":
            self._save_from_review()

    def action_regenerate(self) -> None:
        """Regenerate the spec from the original description."""
        if self.phase in ("review", "error") and self._last_description:
            # Reset state
            self._extracted_json = None
            output_log = self.query_one("#output", RichLog)
            output_log.clear()
            self._start_agent(self._last_description)

    def action_cancel(self) -> None:
        if self._agent_task and not self._agent_task.done():
            self._agent_task.cancel()
        if self._agent:
            asyncio.create_task(self._agent.stop())
        self.dismiss(None)

    def _start_agent(self, description: str) -> None:
        self.phase = "thinking"
        output = self.query_one("#output", RichLog)
        output.write("[dim]Starting agent...[/dim]")

        self._agent_task = asyncio.create_task(self._run_prd_agent(description))

    async def _run_prd_agent(self, description: str) -> None:
        """Run the AI agent to create a PRD spec."""
        output = self.query_one("#output", RichLog)

        # Ensure specs directory exists
        specs_dir = self._gk_dir / "specs"
        specs_dir.mkdir(parents=True, exist_ok=True)

        # Generate filename from description
        filename = re.sub(r"[^a-z0-9]+", "-", description.lower())[:50].strip("-")
        filename = f"{filename}.json"
        self._spec_path = specs_dir / filename

        # Build prompt for PRD creation
        prompt = self._build_prd_prompt(description)

        # Use streaming mode for real-time output
        self._agent = ClaudeAgent(
            workspace=Path.cwd(),
            allow_file_creation=False,  # Use streaming mode
        )

        try:
            async for event in self._agent.run(prompt):
                match event:
                    case TextEvent(text=text):
                        # Display streaming text and force UI refresh
                        if text.strip():
                            output.write(text.rstrip("\n"))
                        self.refresh()
                        # Better UI responsiveness with small sleep
                        await asyncio.sleep(0.01)

                    case ErrorEvent(message=msg):
                        output.write(f"\n[red]Error: {msg}[/red]")
                        self.refresh()

                    case CompleteEvent(success=success, output=full_output):
                        if success:
                            # Extract JSON from output
                            extracted = self._extract_json(full_output)
                            if extracted:
                                self._extracted_json = extracted
                                # Show in review editor
                                review_editor = self.query_one("#review-editor", TextArea)
                                review_editor.text = json.dumps(extracted, indent=2)
                                self.phase = "review"
                                output.write(
                                    "\n[green]Spec generated - review and edit below[/green]"
                                )
                            else:
                                self.phase = "error"
                                output.write(
                                    "\n[yellow]Could not extract PRD JSON from response.[/yellow]"
                                )
                        else:
                            self.phase = "error"
                            output.write("\n[red]Agent failed.[/red]")
                        self.refresh()

        except asyncio.CancelledError:
            output.write("\n[dim]Cancelled[/dim]")
        except Exception as e:
            self.phase = "error"
            output.write(f"\n[red]Error: {e}[/red]")
        finally:
            self._agent = None

    def _build_prd_prompt(self, description: str) -> str:
        """Build the prompt for PRD creation."""
        return f"""Create a PRD JSON for the following feature. Output ONLY valid JSON, no markdown code blocks, no explanation.

Feature: {description}

Required JSON format (output exactly this structure):
{{
  "project": "groundskeeper",
  "branchName": "groundskeeper/<feature-slug>",
  "description": "<one line description>",
  "userStories": [
    {{
      "id": "US-001",
      "title": "<story title>",
      "description": "<what to implement>",
      "acceptanceCriteria": [
        "<specific testable criterion>",
        "Typecheck passes"
      ],
      "priority": "high",
      "passes": false,
      "notes": ""
    }}
  ]
}}

Output the JSON now:"""

    def _extract_json(self, text: str) -> dict | None:
        """Extract JSON from text."""
        # Try to find JSON in code blocks first
        json_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
        if json_match:
            json_str = json_match.group(1)
        else:
            # Try to find raw JSON object
            json_match = re.search(r"(\{[\s\S]*\})", text)
            if json_match:
                json_str = json_match.group(1)
            else:
                return None

        try:
            parsed = json.loads(json_str)
            # Validate it has required fields
            if "userStories" not in parsed:
                return None
            return parsed
        except json.JSONDecodeError:
            return None

    def _validate_review_json(self) -> tuple[bool, str, dict | None]:
        """Validate the JSON in the review editor."""
        editor = self.query_one("#review-editor", TextArea)
        json_str = editor.text

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

    def _save_from_review(self) -> None:
        """Save the spec from the review editor."""
        is_valid, message, parsed = self._validate_review_json()
        self.is_valid = is_valid
        self.validation_status = message

        if is_valid and parsed and self._spec_path:
            try:
                self._spec_path.write_text(json.dumps(parsed, indent=2), encoding="utf-8")
                self._created_path = self._spec_path
                self.phase = "complete"
                self.validation_status = f"Saved: {self._spec_path.name}"
            except OSError as e:
                self.is_valid = False
                self.validation_status = f"Save failed: {e}"

    def key_a(self) -> None:
        """Activate the created spec."""
        if self.phase == "complete" and self._created_path:
            self.dismiss(self._created_path)

    def key_s(self) -> None:
        """View in specs browser (only in complete phase)."""
        if self.phase == "complete":
            self.dismiss(None)
            # Parent app will open specs screen
