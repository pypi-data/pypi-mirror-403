"""Claude CLI agent implementation.

Wraps the `claude` CLI tool and translates its output into AgentEvent protocol.
"""

import asyncio
import json
from collections.abc import AsyncIterator
from pathlib import Path

from groundskeeper.ansi import strip_ansi

from .protocol import (
    AgentEvent,
    AgentProtocol,
    CompleteEvent,
    ErrorEvent,
    TextEvent,
)


class ClaudeAgent(AgentProtocol):
    """Agent implementation for Claude CLI.

    Supports two modes:
    - Streaming mode (--print --output-format stream-json): Real-time output, no file creation
    - Interactive mode (no --print): Can create files, but output only at end

    Args:
        workspace: Working directory for the agent
        allow_file_creation: If True, runs without --print to allow tool use
        dangerously_skip_permissions: Skip permission prompts (for trusted environments)
    """

    def __init__(
        self,
        workspace: Path | None = None,
        allow_file_creation: bool = False,
        dangerously_skip_permissions: bool = True,
    ) -> None:
        self._workspace = workspace or Path.cwd()
        self._allow_file_creation = allow_file_creation
        self._skip_permissions = dangerously_skip_permissions
        self._process: asyncio.subprocess.Process | None = None

    @property
    def name(self) -> str:
        return "Claude"

    @property
    def supports_streaming(self) -> bool:
        # Streaming works best in print mode
        return not self._allow_file_creation

    @property
    def supports_file_creation(self) -> bool:
        return self._allow_file_creation

    async def run(self, prompt: str) -> AsyncIterator[AgentEvent]:
        """Execute prompt and stream events."""
        cmd = ["claude"]

        if self._skip_permissions:
            cmd.append("--dangerously-skip-permissions")

        if not self._allow_file_creation:
            # Streaming mode - real-time output
            # Note: stream-json requires --verbose
            cmd.extend(["--print", "--output-format", "stream-json", "--verbose"])

        try:
            self._process = await asyncio.create_subprocess_exec(
                *cmd,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
                cwd=self._workspace,
            )
        except FileNotFoundError:
            yield ErrorEvent(message="claude CLI not found in PATH", recoverable=False)
            yield CompleteEvent(success=False)
            return

        # Send prompt to stdin
        if self._process.stdin:
            self._process.stdin.write(prompt.encode())
            await self._process.stdin.drain()
            self._process.stdin.close()

        full_output = ""

        if self._process.stdout:
            if not self._allow_file_creation:
                # Parse streaming JSON
                async for event in self._parse_stream_json(self._process.stdout):
                    if isinstance(event, TextEvent):
                        full_output += event.text
                    yield event
            else:
                # Raw output mode (interactive) - collect and emit at end
                async for event in self._parse_raw_output(self._process.stdout):
                    if isinstance(event, TextEvent):
                        full_output += event.text
                    yield event

        returncode = await self._process.wait()
        self._process = None

        yield CompleteEvent(
            success=returncode == 0,
            output=full_output,
        )

    async def _parse_stream_json(self, stdout: asyncio.StreamReader) -> AsyncIterator[AgentEvent]:
        """Parse Claude's stream-json output format.

        Claude's stream-json format (with --verbose) emits:
        - {"type":"system","subtype":"init",...} - session init
        - {"type":"content_block_delta",...} - streaming text chunks (for long responses)
        - {"type":"assistant","message":{...}} - full message (for short responses or final)
        - {"type":"result","subtype":"success",...} - completion
        """
        buffer = ""
        emitted_text = ""  # Track what we've already emitted

        while True:
            chunk = await stdout.read(1024)
            if not chunk:
                break
            buffer += chunk.decode("utf-8", errors="replace")

            # Process complete JSON lines
            while "\n" in buffer:
                line, buffer = buffer.split("\n", 1)
                line = line.strip()
                if not line:
                    continue

                try:
                    event = json.loads(line)
                    event_type = event.get("type", "")

                    if event_type == "content_block_delta":
                        # Streaming text chunk
                        delta = event.get("delta", {})
                        if delta.get("type") == "text_delta":
                            text = delta.get("text", "")
                            if text:
                                emitted_text += text
                                yield TextEvent(text=text)

                    elif event_type == "assistant":
                        # Full message - extract text from content blocks
                        content = event.get("message", {}).get("content", [])
                        for block in content:
                            if block.get("type") == "text":
                                text = block.get("text", "")
                                # Only emit if not already streamed via deltas
                                if text and text not in emitted_text:
                                    emitted_text += text
                                    yield TextEvent(text=text)

                    elif event_type == "error":
                        error_msg = event.get("error", {}).get("message", "Unknown error")
                        yield ErrorEvent(message=error_msg)

                    # Ignore "system" and "result" types - handled by CompleteEvent

                except json.JSONDecodeError:
                    # Partial JSON, put back in buffer
                    buffer = line + "\n" + buffer
                    break

    async def _parse_raw_output(self, stdout: asyncio.StreamReader) -> AsyncIterator[AgentEvent]:
        """Parse raw output from interactive mode."""
        while True:
            chunk = await stdout.read(1024)
            if not chunk:
                break
            text = chunk.decode("utf-8", errors="replace")

            # Filter out ANSI escape sequences for cleaner display
            # But still emit the text for now
            clean = strip_ansi(text)
            if clean.strip():
                yield TextEvent(text=clean)

    async def stop(self) -> None:
        """Stop the running process."""
        if self._process:
            self._process.terminate()
            try:
                await asyncio.wait_for(self._process.wait(), timeout=5.0)
            except TimeoutError:
                self._process.kill()
            self._process = None
