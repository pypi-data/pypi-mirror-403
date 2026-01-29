"""Generic agent implementation for any CLI tool.

Provides GenericAgent that runs CLI tools in a PTY, preserving TTY behavior
and ANSI colors. Follows the groundskeeper-orchestrator pattern.
"""

import asyncio
import os
import pty
import selectors
import tempfile
from collections.abc import AsyncIterator
from contextlib import suppress
from dataclasses import dataclass
from functools import partial
from pathlib import Path
from typing import Literal

from groundskeeper.constants import LARGE_PROMPT_THRESHOLD, PROCESS_STOP_TIMEOUT, PTY_READ_TIMEOUT

from .protocol import (
    AgentEvent,
    AgentProtocol,
    CompleteEvent,
    ErrorEvent,
    TextEvent,
)


@dataclass
class BackendConfig:
    """Configuration for a CLI backend tool.

    Args:
        command: Base command to execute (e.g., "opencode", "kiro-cli")
        args: Additional arguments before the prompt (e.g., ["run"], ["chat", "--no-interactive"])
        prompt_flag: Flag for passing prompt (e.g., "-p", "--prompt"), or None for positional
        prompt_mode: How to pass the prompt - "arg" for command line, "stdin" for standard input
    """

    command: str
    args: list[str]
    prompt_flag: str | None
    prompt_mode: Literal["arg", "stdin"]


class GenericAgent(AgentProtocol):
    """Generic agent that runs CLI tools in a PTY with proper resource management."""

    def __init__(
        self,
        config: BackendConfig,
        workspace: Path | None = None,
        name_override: str | None = None,
    ) -> None:
        self._config = config
        self._workspace = workspace or Path.cwd()
        self._name = name_override or config.command
        self._process: asyncio.subprocess.Process | None = None
        self._master_fd: int | None = None
        self._stopping = False

    @property
    def name(self) -> str:
        return self._name

    @property
    def supports_streaming(self) -> bool:
        return True

    @property
    def supports_file_creation(self) -> bool:
        return True

    def _read_with_timeout(self, fd: int, timeout: float = PTY_READ_TIMEOUT) -> bytes:
        """Read from fd with timeout using select. Returns empty bytes on timeout."""
        sel = selectors.DefaultSelector()
        try:
            sel.register(fd, selectors.EVENT_READ)
            events = sel.select(timeout=timeout)
            if events:
                return os.read(fd, 4096)
            return b""
        finally:
            sel.close()

    async def run(self, prompt: str) -> AsyncIterator[AgentEvent]:
        """Execute prompt and stream output. Uses try/finally for guaranteed cleanup."""
        master_fd: int | None = None
        slave_fd: int | None = None
        temp_file: Path | None = None

        try:
            cmd = [self._config.command, *self._config.args]
            prompt_to_use = prompt

            if len(prompt) > LARGE_PROMPT_THRESHOLD and self._config.prompt_mode == "arg":
                try:
                    fd, temp_path = tempfile.mkstemp(suffix=".txt", prefix="gk_prompt_")
                    temp_file = Path(temp_path)
                    os.write(fd, prompt.encode("utf-8"))
                    os.close(fd)
                    prompt_to_use = str(temp_file)
                except OSError as e:
                    yield ErrorEvent(f"Failed to create temp file: {e}", recoverable=False)
                    yield CompleteEvent(success=False)
                    return

            if self._config.prompt_mode == "arg":
                if self._config.prompt_flag:
                    cmd.extend([self._config.prompt_flag, prompt_to_use])
                else:
                    cmd.append(prompt_to_use)

            try:
                master_fd, slave_fd = pty.openpty()
                self._master_fd = master_fd
            except OSError as e:
                yield ErrorEvent(f"Failed to create PTY: {e}", recoverable=False)
                yield CompleteEvent(success=False)
                return

            try:
                self._process = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdin=slave_fd,
                    stdout=slave_fd,
                    stderr=slave_fd,
                    cwd=self._workspace,
                )
            except FileNotFoundError:
                yield ErrorEvent(f"{self._config.command} not found", recoverable=False)
                yield CompleteEvent(success=False)
                return
            except OSError as e:
                yield ErrorEvent(f"Failed to start {self._config.command}: {e}", recoverable=False)
                yield CompleteEvent(success=False)
                return

            os.close(slave_fd)
            slave_fd = None

            if self._config.prompt_mode == "stdin":
                try:
                    loop = asyncio.get_running_loop()
                    await loop.run_in_executor(None, partial(os.write, master_fd, prompt.encode()))
                    await loop.run_in_executor(None, partial(os.write, master_fd, b"\x04"))
                except OSError as e:
                    yield ErrorEvent(f"Failed to write prompt: {e}", recoverable=True)

            output_parts: list[str] = []
            loop = asyncio.get_running_loop()

            while not self._stopping:
                try:
                    chunk = await loop.run_in_executor(
                        None, partial(self._read_with_timeout, master_fd)
                    )
                except OSError:
                    break

                if not chunk:
                    # Check if process exited
                    if self._process.returncode is not None:
                        break
                    continue

                text = chunk.decode("utf-8", errors="replace")
                output_parts.append(text)
                yield TextEvent(text=text)

            returncode = await self._process.wait() if self._process else 1
            yield CompleteEvent(success=returncode == 0, output="".join(output_parts))

        finally:
            if slave_fd is not None:
                with suppress(OSError):
                    os.close(slave_fd)
            if master_fd is not None:
                with suppress(OSError):
                    os.close(master_fd)
            self._master_fd = None
            self._process = None
            if temp_file:
                temp_file.unlink(missing_ok=True)

    async def stop(self) -> None:
        """Stop the running process gracefully."""
        self._stopping = True
        if self._process:
            self._process.terminate()
            try:
                await asyncio.wait_for(self._process.wait(), timeout=PROCESS_STOP_TIMEOUT)
            except TimeoutError:
                self._process.kill()
                await self._process.wait()
