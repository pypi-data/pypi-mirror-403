"""Inye-ADK CLI commands."""

import os
import shutil
from pathlib import Path

import click
from rich.console import Console
from rich.panel import Panel

console = Console()

TEMPLATES_DIR = Path(__file__).parent / "templates"


@click.group()
@click.version_option()
def main():
    """Inye Agentic Development Kit

    Intent clarification skill for Claude Code.
    """
    pass


@main.command()
@click.argument("path", default=".", type=click.Path())
@click.option("-y", "--non-interactive", is_flag=True, help="Non-interactive mode")
@click.option("--force", is_flag=True, help="Force reinitialize without confirmation")
def init(path: str, non_interactive: bool, force: bool):
    """Initialize Inye-ADK in a project.

    Installs the /intent skill for Claude Code.
    """
    target_path = Path(path).resolve()
    claude_skills_dir = target_path / ".claude" / "skills"
    intent_skill_dir = claude_skills_dir / "intent"

    console.print()
    console.print(Panel.fit(
        "[bold blue]Inye-ADK Initializer[/bold blue]\n"
        "Intent Clarification Skill for Claude Code",
        border_style="blue"
    ))
    console.print()

    # Check if already initialized
    if intent_skill_dir.exists() and not force:
        if non_interactive:
            console.print("[yellow]Warning:[/yellow] /intent skill already exists. Use --force to overwrite.")
            return
        if not click.confirm("The /intent skill already exists. Overwrite?"):
            console.print("[dim]Cancelled.[/dim]")
            return

    # Create .claude/skills directory
    claude_skills_dir.mkdir(parents=True, exist_ok=True)

    # Copy intent skill template
    intent_template_dir = TEMPLATES_DIR / "skills" / "intent"
    if intent_skill_dir.exists():
        shutil.rmtree(intent_skill_dir)
    shutil.copytree(intent_template_dir, intent_skill_dir)

    console.print(f"[green]OK[/green] Installed /intent skill to {intent_skill_dir.relative_to(target_path)}")
    console.print()
    console.print("[bold]Usage:[/bold]")
    console.print("  In Claude Code, type: [cyan]/intent[/cyan] [dim]<your request>[/dim]")
    console.print()
    console.print("[dim]Example:[/dim]")
    console.print("  [cyan]/intent[/cyan] Add a logout button to the header")
    console.print()


@main.command()
def status():
    """Show Inye-ADK status in current project."""
    cwd = Path.cwd()
    intent_skill_dir = cwd / ".claude" / "skills" / "intent"

    console.print()
    if intent_skill_dir.exists():
        console.print("[green]OK[/green] /intent skill is installed")
        skill_md = intent_skill_dir / "SKILL.md"
        if skill_md.exists():
            console.print(f"[dim]Location: {intent_skill_dir}[/dim]")
    else:
        console.print("[yellow]Not initialized[/yellow]")
        console.print("[dim]Run 'inye init' to install the /intent skill[/dim]")
    console.print()


if __name__ == "__main__":
    main()
