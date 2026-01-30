"""User input and interactive prompt handling."""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING, Literal

from rich.prompt import Prompt

if TYPE_CHECKING:
    from rich.console import Console


ActionChoice = Literal["accept", "reject", "edit", "quit", "undo"]

ACTION_MAP: dict[str, ActionChoice] = {
    "a": "accept",
    "accept": "accept",
    "r": "reject",
    "reject": "reject",
    "e": "edit",
    "edit": "edit",
    "q": "quit",
    "quit": "quit",
    "u": "undo",
    "undo": "undo",
}


def get_edit_prompt(console: Console) -> str:
    """Prompt the user for an edit description.

    Returns the user's input string. Returns empty string on EOF.
    """
    console.print()
    try:
        result = Prompt.ask("[bold cyan]What changes do you want?[/bold cyan]")
        return result.strip()
    except EOFError:
        return ""


def get_action(console: Console, undo_available: bool = False) -> ActionChoice:
    """Prompt the user to accept, reject, edit, undo, or quit.

    Returns the chosen action.
    """
    options = "[bold][green]a[/green]ccept [red]r[/red]eject [yellow]e[/yellow]dit"
    if undo_available:
        options += " [magenta]u[/magenta]ndo"
    options += " [dim]q[/dim]uit[/bold]"

    console.print()
    console.print(options)

    while True:
        try:
            choice = Prompt.ask("[bold]>[/bold]").strip().lower()
        except EOFError:
            return "quit"

        if choice in ACTION_MAP:
            action = ACTION_MAP[choice]
            if action == "undo" and not undo_available:
                console.print("[dim]Nothing to undo.[/dim]")
                continue
            return action

        console.print(
            "[dim]Invalid choice. Use a/r/e/q" + ("/u" if undo_available else "") + "[/dim]"
        )


def confirm_overwrite(console: Console, filepath: str) -> bool:
    """Ask user to confirm file overwrite."""
    result = Prompt.ask(
        f"[yellow]Overwrite {filepath}?[/yellow] [dim](y/n)[/dim]",
        choices=["y", "n"],
        default="y",
    )
    return result == "y"


def is_interactive() -> bool:
    """Check if stdin is connected to a terminal."""
    return sys.stdin.isatty()
