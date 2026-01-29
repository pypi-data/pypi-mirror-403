"""Inye-ADK CLI commands."""

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

    Intent clarification command for Claude Code.
    """
    pass


@main.command()
@click.argument("path", default=".", type=click.Path())
@click.option("-y", "--non-interactive", is_flag=True, help="Non-interactive mode")
@click.option("--force", is_flag=True, help="Force reinitialize without confirmation")
def init(path: str, non_interactive: bool, force: bool):
    """Initialize Inye-ADK in a project.

    Installs the /inye:intent command for Claude Code.
    """
    target_path = Path(path).resolve()
    claude_commands_dir = target_path / ".claude" / "commands"
    inye_commands_dir = claude_commands_dir / "inye"
    intent_file = inye_commands_dir / "intent.md"

    console.print()
    console.print(Panel.fit(
        "[bold blue]Inye-ADK Initializer[/bold blue]\n"
        "Intent Clarification Command for Claude Code",
        border_style="blue"
    ))
    console.print()

    # Check if already initialized
    if intent_file.exists() and not force:
        if non_interactive:
            console.print("[yellow]Warning:[/yellow] /inye:intent command already exists. Use --force to overwrite.")
            return
        if not click.confirm("The /inye:intent command already exists. Overwrite?"):
            console.print("[dim]Cancelled.[/dim]")
            return

    # Create .claude/commands/inye directory
    inye_commands_dir.mkdir(parents=True, exist_ok=True)

    # Copy intent command template
    intent_template = TEMPLATES_DIR / "commands" / "inye" / "intent.md"
    shutil.copy2(intent_template, intent_file)

    console.print(f"[green]OK[/green] Installed /inye:intent command to {inye_commands_dir.relative_to(target_path)}")
    console.print()
    console.print("[bold]Usage:[/bold]")
    console.print("  In Claude Code, type: [cyan]/inye:intent[/cyan] [dim]<your request>[/dim]")
    console.print()
    console.print("[dim]Example:[/dim]")
    console.print("  [cyan]/inye:intent[/cyan] Add a logout button to the header")
    console.print()


@main.command()
def status():
    """Show Inye-ADK status in current project."""
    cwd = Path.cwd()
    intent_file = cwd / ".claude" / "commands" / "inye" / "intent.md"

    console.print()
    if intent_file.exists():
        console.print("[green]OK[/green] /inye:intent command is installed")
        console.print(f"[dim]Location: {intent_file}[/dim]")
    else:
        console.print("[yellow]Not initialized[/yellow]")
        console.print("[dim]Run 'inye init' to install the /inye:intent command[/dim]")
    console.print()


if __name__ == "__main__":
    main()
