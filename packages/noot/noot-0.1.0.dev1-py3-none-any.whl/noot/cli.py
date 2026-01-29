#!/usr/bin/env python3
"""CLI for noot projects."""

import argparse
import re
import sys
from pathlib import Path


def validate_project_name(name: str) -> bool:
    """Validate project name: lowercase, underscores, starts with letter."""
    return bool(re.match(r"^[a-z][a-z0-9_]*$", name))


def cmd_init(args):
    """Initialize a noot project in the current directory."""
    from rich.console import Console
    from rich.prompt import Prompt

    from noot.init import init_project

    console = Console()

    # Use --name if provided, otherwise prompt interactively
    if args.name:
        project_name = args.name
        if not validate_project_name(project_name):
            console.print(
                "[red]Invalid name. Use lowercase letters, numbers, underscores. "
                "Must start with a letter.[/red]"
            )
            sys.exit(1)
    else:
        console.print("\n[bold blue]Noot Project Setup[/bold blue]\n")
        while True:
            project_name = Prompt.ask("[green]Project name[/green]")
            if validate_project_name(project_name):
                break
            console.print(
                "[red]Invalid name. Use lowercase letters, numbers, underscores. "
                "Must start with a letter.[/red]"
            )

    try:
        init_project(Path.cwd(), project_name)
        msg = f"[bold green]Project '{project_name}' initialized![/bold green]"
        console.print(f"\n{msg}")
        console.print("\n[dim]Created:[/dim]")
        console.print(f"  src/{project_name}/__init__.py")
        console.print(f"  cli/{project_name}.py")
        console.print(f"  tests/test_{project_name}.py")
        console.print("  .cassettes/cli/")
        console.print("  .cassettes/http/")
        console.print("  pyproject.toml")
        console.print("\n[dim]Next steps:[/dim]")
        console.print(f"  1. Edit cli/{project_name}.py with your CLI")
        console.print(f"  2. Edit tests/test_{project_name}.py with your tests")
        console.print("  3. Set ANTHROPIC_API_KEY environment variable")
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        prog="noot",
        description="Noot - Test interactive CLIs with LLM-driven flows",
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # init command
    init_parser = subparsers.add_parser(
        "init", help="Initialize a noot example project"
    )
    init_parser.add_argument(
        "--name", "-n",
        help="Project name (skips interactive prompt)"
    )
    init_parser.set_defaults(func=cmd_init)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(0)

    args.func(args)


if __name__ == "__main__":
    main()
