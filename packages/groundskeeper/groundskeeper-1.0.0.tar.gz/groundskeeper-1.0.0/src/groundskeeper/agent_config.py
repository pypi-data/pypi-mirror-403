"""Agent configuration loader for TOML-based agent definitions.

This module provides type-safe loading and validation of agent configuration files.
Each agent backend (Claude, OpenCode, Aider, Codex) is defined in a TOML file
under src/groundskeeper/data/agents/.

Example:
    >>> config = load_agent_config("claude")
    >>> print(config["agent"]["name"])
    'Claude Code'
    >>> agents = list_available_agents()
    >>> print(agents)
    ['aider', 'claude', 'codex', 'opencode']
"""

import tomllib
from typing import Literal, TypedDict

from groundskeeper.data import AGENTS_DIR


# Type definitions for agent configuration structure
class EnvironmentVar(TypedDict, total=False):
    """Configuration for an environment variable."""

    required: bool
    description: str


class AgentMetadata(TypedDict):
    """Agent metadata section."""

    name: str
    short_name: str
    command: str
    description: str


class AgentArguments(TypedDict, total=False):
    """Agent command-line arguments section."""

    prompt_flag: str
    workspace_flag: str
    file_creation_flag: str
    yes_flag: str
    no_git_flag: str
    model_flag: str
    message_flag: str


class AgentExecution(TypedDict, total=False):
    """Agent execution configuration section."""

    args: list[str]
    prompt_mode: Literal["arg", "stdin"]


class AgentPatterns(TypedDict, total=False):
    """Agent output parsing patterns section."""

    thinking: str
    error: str
    file_created: str


class AgentEnvironment(TypedDict, total=False):
    """Agent environment variables section."""

    OPENAI_API_KEY: EnvironmentVar
    ANTHROPIC_API_KEY: EnvironmentVar


class AgentConfig(TypedDict):
    """Complete agent configuration structure.

    This represents the full parsed TOML configuration for an agent.
    """

    agent: AgentMetadata
    arguments: AgentArguments | None
    execution: AgentExecution | None
    environment: AgentEnvironment | None
    patterns: AgentPatterns | None


# Type alias for simpler usage
type AgentName = str


def load_agent_config(name: str) -> AgentConfig:
    """Load and parse an agent configuration file.

    Args:
        name: The agent's short name (e.g., 'claude', 'opencode')
              Corresponds to the TOML filename without extension.

    Returns:
        Parsed agent configuration as an AgentConfig TypedDict

    Raises:
        FileNotFoundError: If the configuration file doesn't exist
        tomllib.TOMLDecodeError: If the TOML file is malformed
        KeyError: If required configuration fields are missing

    Example:
        >>> config = load_agent_config("claude")
        >>> print(config["agent"]["command"])
        'claude'
    """
    config_path = AGENTS_DIR / f"{name}.toml"

    if not config_path.exists():
        available = ", ".join(list_available_agents())
        raise FileNotFoundError(
            f"Agent configuration '{name}' not found. Available agents: {available}"
        )

    with config_path.open("rb") as f:
        data = tomllib.load(f)

    # Validate required top-level structure
    if "agent" not in data:
        raise KeyError(f"Configuration file {config_path} missing required 'agent' section")

    # Validate required agent metadata fields
    required_fields = {"name", "short_name", "command", "description"}
    missing_fields = required_fields - set(data["agent"].keys())
    if missing_fields:
        raise KeyError(f"Agent configuration missing required fields: {', '.join(missing_fields)}")

    # Return with optional sections, defaulting to None if not present
    return AgentConfig(
        agent=data["agent"],
        arguments=data.get("agent", {}).get("arguments"),
        execution=data.get("agent", {}).get("execution"),
        environment=data.get("agent", {}).get("environment"),
        patterns=data.get("agent", {}).get("patterns"),
    )


def list_available_agents() -> list[str]:
    """List all available agent configurations.

    Returns:
        Sorted list of agent short names (without .toml extension)

    Example:
        >>> agents = list_available_agents()
        >>> print(agents)
        ['aider', 'claude', 'codex', 'opencode']
    """
    if not AGENTS_DIR.exists():
        return []

    agent_files = AGENTS_DIR.glob("*.toml")
    return sorted(path.stem for path in agent_files)


def get_agent_command(name: str) -> str:
    """Get the executable command for an agent.

    Args:
        name: The agent's short name

    Returns:
        The command to execute the agent

    Example:
        >>> cmd = get_agent_command("claude")
        >>> print(cmd)
        'claude'
    """
    config = load_agent_config(name)
    return config["agent"]["command"]


def get_agent_description(name: str) -> str:
    """Get the description for an agent.

    Args:
        name: The agent's short name

    Returns:
        Human-readable description of the agent

    Example:
        >>> desc = get_agent_description("claude")
        >>> print(desc)
        'Anthropic's AI coding assistant with direct terminal integration'
    """
    config = load_agent_config(name)
    return config["agent"]["description"]


def load_backend_config(name: str):
    """Load a BackendConfig from TOML configuration.

    Args:
        name: The agent's short name (e.g., 'opencode', 'kiro')

    Returns:
        BackendConfig instance for use with GenericAgent

    Example:
        >>> config = load_backend_config("opencode")
        >>> print(config.command)
        'opencode'
    """
    # Import here to avoid circular dependency
    from groundskeeper.agents.generic import BackendConfig

    config = load_agent_config(name)
    exec_cfg = config.get("execution") or {}
    args_cfg = config.get("arguments") or {}

    return BackendConfig(
        command=config["agent"]["command"],
        args=exec_cfg.get("args", []),
        prompt_flag=args_cfg.get("prompt_flag") or None,
        prompt_mode=exec_cfg.get("prompt_mode", "arg"),
    )
