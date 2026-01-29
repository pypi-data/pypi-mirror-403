"""Agent runner for iteration loops."""

import asyncio
from collections.abc import Callable
from pathlib import Path
from typing import Literal

from groundskeeper.agent_config import load_backend_config
from groundskeeper.agents import (
    AgentProtocol,
    ClaudeAgent,
    CompleteEvent,
    ErrorEvent,
    GenericAgent,
    TextEvent,
)
from groundskeeper.ansi import strip_ansi
from groundskeeper.prompts import get_prompt
from groundskeeper.state import Status

# Backend type using PEP 695 type alias syntax
type BackendType = Literal["claude", "opencode", "kiro", "gemini", "codex", "amp", "copilot"]


def create_agent(
    backend: BackendType,
    workspace: Path,
    allow_file_creation: bool = False,
) -> AgentProtocol:
    """Create an agent for the specified backend.

    Args:
        backend: Backend type to use ("claude", "opencode", etc.)
        workspace: Working directory for the agent
        allow_file_creation: For Claude, whether to allow file creation mode

    Returns:
        Configured agent instance
    """
    if backend == "claude":
        return ClaudeAgent(
            workspace=workspace,
            allow_file_creation=allow_file_creation,
        )

    # For all other backends, load config from TOML and use GenericAgent
    config = load_backend_config(backend)
    return GenericAgent(config=config, workspace=workspace)


async def run_iteration(
    workspace: Path,
    on_output: Callable[[str], None],
    backend: BackendType = "claude",
    is_paused: Callable[[], bool] | None = None,
) -> tuple[Status, int]:
    """Run a single iteration using the configured agent.

    Args:
        workspace: Working directory for the agent
        on_output: Callback for streaming output
        backend: Backend type to use
        is_paused: Optional callback that returns True if execution should pause

    Returns:
        Tuple of (Status, returncode)
    """
    prompt = get_prompt()
    agent = create_agent(backend, workspace)
    output_parts: list[str] = []
    returncode = 0

    try:
        async for event in agent.run(prompt):
            # Check if paused and wait until resumed
            if is_paused is not None:
                while is_paused():
                    await asyncio.sleep(0.2)

            match event:
                case TextEvent(text=text):
                    # For non-claude backends, optionally clean up output
                    if backend != "claude":
                        # Strip ANSI for the stored output (for COMPLETE detection)
                        clean_text = strip_ansi(text)
                        output_parts.append(clean_text)
                    else:
                        output_parts.append(text)
                    # Always display the original text (with colors)
                    on_output(text)
                case ErrorEvent(message=msg):
                    on_output(f"\nError: {msg}\n")
                    returncode = 1
                case CompleteEvent(success=success, output=full_output):
                    if not success:
                        returncode = 1
                    if full_output:
                        output_parts.clear()
                        # Strip ANSI from full output for pattern matching
                        if backend != "claude":
                            output_parts.append(strip_ansi(full_output))
                        else:
                            output_parts.append(full_output)
    except asyncio.CancelledError:
        await agent.stop()
        raise
    except Exception as e:
        on_output(f"\nException: {e}\n")
        return Status.ERROR, 1
    finally:
        await agent.stop()

    output = "".join(output_parts)
    if "<promise>COMPLETE</promise>" in output:
        return Status.COMPLETE, returncode
    return Status.RUNNING if returncode == 0 else Status.ERROR, returncode
