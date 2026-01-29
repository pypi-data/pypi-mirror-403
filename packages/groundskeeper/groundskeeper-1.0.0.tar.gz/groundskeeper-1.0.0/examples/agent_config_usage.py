"""Example usage of the TOML-based agent configuration system.

This demonstrates how to:
1. List all available agents
2. Load agent configurations
3. Access agent metadata and settings
4. Use configurations to initialize agents
"""

from groundskeeper.agent_config import (
    get_agent_description,
    list_available_agents,
    load_agent_config,
)


def main():
    """Demonstrate agent configuration system usage."""
    # List all available agents
    print("Available Agents:")
    print("=" * 60)
    agents = list_available_agents()
    for agent in agents:
        desc = get_agent_description(agent)
        print(f"  {agent}: {desc}")

    print("\n" + "=" * 60)

    # Load and display detailed configuration for each agent
    for agent_name in agents:
        print(f"\n{agent_name.upper()} Configuration:")
        print("-" * 60)

        config = load_agent_config(agent_name)

        # Agent metadata
        print(f"Name:        {config['agent']['name']}")
        print(f"Short Name:  {config['agent']['short_name']}")
        print(f"Command:     {config['agent']['command']}")
        print(f"Description: {config['agent']['description']}")

        # Arguments (if present)
        if config.get("arguments"):
            print("\nArguments:")
            for key, value in config["arguments"].items():
                print(f"  {key}: {value}")

        # Environment variables (if present)
        if config.get("environment"):
            print("\nEnvironment Variables:")
            for var_name, var_config in config["environment"].items():
                required = var_config.get("required", False)
                description = var_config.get("description", "")
                status = "REQUIRED" if required else "OPTIONAL"
                print(f"  {var_name} ({status}): {description}")

        # Patterns (if present)
        if config.get("patterns"):
            print("\nOutput Patterns:")
            for pattern_name, pattern in config["patterns"].items():
                print(f"  {pattern_name}: {pattern}")

    # Example: Using configuration to build a command
    print("\n" + "=" * 60)
    print("\nExample: Building a Claude command:")
    print("-" * 60)
    claude_config = load_agent_config("claude")
    cmd = claude_config["agent"]["command"]
    args = claude_config.get("arguments", {})

    prompt_flag = args.get("prompt_flag", "--prompt")
    workspace_flag = args.get("workspace_flag", "--cwd")

    example_cmd = f"{cmd} {prompt_flag} 'Write a hello world program' {workspace_flag} /path/to/workspace"
    print(f"Command: {example_cmd}")


if __name__ == "__main__":
    main()
