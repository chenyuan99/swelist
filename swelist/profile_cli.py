"""Profile subcommands for swelist CLI."""

import os
import typer
from pathlib import Path
from typing import Optional, Annotated
from rich import print

from swelist.profile import build_profile_report

profile_app = typer.Typer(help="Manage and export your career profile")


def _get_profile_path() -> str:
    """Get the path to profile.md in the skills directory."""
    home = os.path.expanduser("~")
    return os.path.join(home, ".claude", "profile.md")


@profile_app.command()
def report(
    output: Annotated[
        Optional[str], typer.Option(help="Output HTML file path (default: reports/profile.html)")
    ] = None,
):
    """Generate an HTML profile report from profile.md"""
    profile_path = _get_profile_path()

    if not os.path.exists(profile_path):
        print(f"[red]Error: Profile not found at {profile_path}[/red]")
        print("Run a job search skill first, or create a profile.md file in ~/.claude/")
        raise typer.Exit(1)

    if output is None:
        output = "reports/profile.html"

    try:
        result = build_profile_report(profile_path, output)
        print(f"[green]✓[/green] Profile report generated: [bold]{result['generated']}[/bold]")
    except Exception as e:
        print(f"[red]Error generating profile report:[/red] {e}")
        raise typer.Exit(1)
