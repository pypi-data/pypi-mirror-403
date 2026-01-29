import argparse
import asyncio
import sys
from pathlib import Path
from typing import cast

from groundskeeper.app import GroundskeeperApp
from groundskeeper.parser import parse_prd
from groundskeeper.runner import BackendType, run_iteration
from groundskeeper.specmanager import SpecManager
from groundskeeper.state import Status

COMMAND_HELP: dict[str, dict[str, str]] = {
    "help": {
        "description": "Show help information for groundskeeper or a specific command",
        "usage": "groundskeeper help [COMMAND]",
        "options": "",
        "examples": """    groundskeeper help                 Show general help
    groundskeeper help spec            Show detailed help for --spec
    groundskeeper help backend         Show detailed help for --backend""",
    },
    "spec": {
        "description": "Specify which spec to run. Can be a spec name or direct path to a prd.json file.",
        "usage": "groundskeeper --spec <NAME|PATH>",
        "options": """    NAME    Name of a spec in .groundskeeper/specs/ (without .json extension)
    PATH    Direct path to a prd.json file""",
        "examples": """    groundskeeper --spec myproject     Run spec named 'myproject'
    groundskeeper --spec ./prd.json    Run with a direct path to prd.json""",
    },
    "list": {
        "description": "List all available specs in the groundskeeper directory.",
        "usage": "groundskeeper --list",
        "options": "",
        "examples": """    groundskeeper --list               Show all specs with their status""",
    },
    "new": {
        "description": "Start the new spec wizard to create a new spec interactively.",
        "usage": "groundskeeper --new",
        "options": "",
        "examples": """    groundskeeper --new                Launch the spec creation wizard""",
    },
    "headless": {
        "description": "Run groundskeeper without the TUI interface. Useful for CI/CD pipelines.",
        "usage": "groundskeeper --headless [OPTIONS]",
        "options": "",
        "examples": """    groundskeeper --headless                       Run in headless mode
    groundskeeper --headless --spec myproject      Run specific spec headlessly""",
    },
    "max-iterations": {
        "description": "Set the maximum number of agent iterations before stopping.",
        "usage": "groundskeeper --max-iterations <N>",
        "options": """    N       Number of iterations (default: 10)""",
        "examples": """    groundskeeper --max-iterations 5       Limit to 5 iterations
    groundskeeper --max-iterations 20      Allow up to 20 iterations""",
    },
    "backend": {
        "description": "Choose which AI agent backend to use for processing.",
        "usage": "groundskeeper --backend <BACKEND>",
        "options": """    claude      Claude Code (default)
    opencode    OpenCode
    kiro        Kiro
    gemini      Gemini
    codex       Codex
    amp         Amp
    copilot     Copilot""",
        "examples": """    groundskeeper --backend gemini     Use Gemini as the agent
    groundskeeper --backend codex      Use Codex as the agent""",
    },
    "dir": {
        "description": "Specify an alternative groundskeeper directory instead of .groundskeeper.",
        "usage": "groundskeeper --dir <PATH>",
        "options": """    PATH    Path to groundskeeper directory""",
        "examples": """    groundskeeper --dir ./my-groundskeeper        Use ./my-groundskeeper as the groundskeeper directory""",
    },
}


def print_help() -> None:
    """Print formatted help information for all available commands."""
    help_text = """
Groundskeeper - Autonomous agent loop interface

USAGE:
    groundskeeper [OPTIONS]
    groundskeeper help [COMMAND]

COMMANDS:
    help                    Show this help message

OPTIONS:
    --spec <NAME|PATH>      Spec name or path to prd.json
    --list                  List all available specs
    --new                   Start the new spec wizard
    --headless              Run in headless mode (no TUI)
    --max-iterations <N>    Maximum iterations (default: 10)
    --backend <BACKEND>     Agent backend to use (default: claude)
                            Choices: claude, opencode, kiro, gemini, codex, amp, copilot
    --dir <PATH>            Groundskeeper directory (default: .groundskeeper)
    -h, --help              Show this help message

EXAMPLES:
    groundskeeper                      Start the TUI with default settings
    groundskeeper --list               List all available specs
    groundskeeper --spec myproject     Run with a specific spec
    groundskeeper --headless           Run without the TUI interface
    groundskeeper --backend gemini     Use Gemini as the agent backend
    groundskeeper help                 Show this help message
    groundskeeper help spec            Show detailed help for --spec
"""
    print(help_text.strip())


def print_command_help(command: str) -> None:
    """Print detailed help for a specific command."""
    cmd = command.lstrip("-")
    if cmd not in COMMAND_HELP:
        print(f"Unknown command: {command}")
        print("Run 'groundskeeper help' to see available commands.")
        sys.exit(1)

    info = COMMAND_HELP[cmd]
    print(f"\n{cmd.upper()}")
    print(f"\n{info['description']}")
    print(f"\nUSAGE:\n    {info['usage']}")
    if info["options"]:
        print(f"\nOPTIONS:\n{info['options']}")
    print(f"\nEXAMPLES:\n{info['examples']}\n")


def main() -> None:
    # Check for help command/flags before argparse
    if len(sys.argv) >= 2 and sys.argv[1] in ("help", "-h", "--help"):
        if len(sys.argv) == 2:
            print_help()
        else:
            print_command_help(sys.argv[2])
        sys.exit(0)

    parser = argparse.ArgumentParser(
        description="Groundskeeper - Autonomous agent loop interface",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        add_help=False,
    )

    parser.add_argument("--max-iterations", type=int, default=10, help="Maximum iterations")
    parser.add_argument("--spec", type=str, default=None, help="Spec name or path to prd.json")
    parser.add_argument(
        "--dir",
        type=Path,
        default=None,
        help="Groundskeeper directory (default: .groundskeeper)",
    )
    parser.add_argument("--headless", action="store_true", help="Run in headless mode")
    parser.add_argument("--new", action="store_true", help="Start with new spec wizard")
    parser.add_argument(
        "--list", action="store_true", dest="list_specs", help="List available specs"
    )
    parser.add_argument(
        "--backend",
        type=str,
        default="claude",
        choices=["claude", "opencode", "kiro", "gemini", "codex", "amp", "copilot"],
        help="Agent backend to use (default: claude)",
    )
    args = parser.parse_args()

    groundskeeper_dir = args.dir or Path.cwd() / ".groundskeeper"
    spec_manager = SpecManager(groundskeeper_dir)
    spec_manager.ensure_structure()

    # Handle --list
    if args.list_specs:
        specs = spec_manager.list_specs()
        if not specs:
            print("No specs found in .groundskeeper/specs/")
            print("Create one with: groundskeeper --new")
        else:
            print("Available specs:")
            for spec in specs:
                indicator = "*" if spec.is_active else " "
                print(
                    f"  {indicator} {spec.name:<20} {spec.passed}/{spec.total} stories [{spec.status}]"
                )
        sys.exit(0)

    # Resolve PRD path
    prd_path: Path | None = None
    if args.spec:
        spec_path = Path(args.spec)
        if spec_path.exists() and spec_path.suffix == ".json":
            # Direct path
            prd_path = spec_path
        else:
            # Look in specs directory
            spec_file = groundskeeper_dir / "specs" / f"{args.spec}.json"
            if spec_file.exists():
                # Activate this spec
                specs = spec_manager.list_specs()
                for spec in specs:
                    if spec.name == args.spec:
                        spec_manager.activate(spec)
                        break
                prd_path = spec_manager.get_active_prd_path()
            else:
                print(f"Spec not found: {args.spec}")
                print("Use --list to see available specs")
                sys.exit(1)

    # Cast backend to BackendType (argparse choices guarantee valid value)
    backend = cast(BackendType, args.backend)

    if args.headless:
        _run_headless(
            args.max_iterations,
            prd_path or spec_manager.get_active_prd_path(),
            backend,
        )
    else:
        app = GroundskeeperApp(
            max_iterations=args.max_iterations,
            prd_path=prd_path,
            groundskeeper_dir=groundskeeper_dir,
            backend=backend,
        )
        app.run()


def _run_headless(max_iterations: int, prd_path: Path, backend: BackendType) -> None:
    """Run groundskeeper in headless mode for CI/CD."""
    print(f"[groundskeeper] Starting: {backend}, max {max_iterations} iterations")

    if not prd_path.exists():
        print(f"[groundskeeper] Error: {prd_path} not found")
        print("[groundskeeper] Use --spec to specify a spec or --list to see available specs")
        sys.exit(1)

    workspace = prd_path.parent.parent.parent  # .groundskeeper/active/prd.json -> workspace
    if not workspace.exists():
        workspace = Path.cwd()

    async def run() -> int:
        for i in range(1, max_iterations + 1):
            stories = parse_prd(prd_path)
            current = next((s for s in stories if not s.passes), None)

            if not current:
                print("[groundskeeper] All stories complete")
                return 0

            print(f"[groundskeeper] Iteration {i}/{max_iterations}")
            print(f"[groundskeeper] Story: {current.id} - {current.title}")

            status, code = await run_iteration(
                workspace,
                lambda t: print(f"[{backend}] {t}", end=""),
                backend=backend,
            )

            if status == Status.COMPLETE:
                print("[groundskeeper] All stories complete")
                return 0
            elif status == Status.ERROR:
                print(f"[groundskeeper] Error: exit code {code}")
                return 1

        print("[groundskeeper] Max iterations reached")
        return 1

    sys.exit(asyncio.run(run()))


if __name__ == "__main__":
    main()
