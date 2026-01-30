"""Diff rendering for terminal display."""

from __future__ import annotations

from typing import TYPE_CHECKING

from rich.panel import Panel
from rich.text import Text

if TYPE_CHECKING:
    from rich.console import Console

    from src.core.diff import DiffResult


def render_diff(console: Console, diff: DiffResult) -> None:
    """Render a unified diff with color-coded additions and deletions."""
    if not diff.has_changes:
        console.print(Text("No changes detected.", style="dim"))
        return

    output = Text()

    for line in diff.unified_diff.splitlines(keepends=True):
        stripped = line.rstrip("\n")

        if line.startswith("+++") or line.startswith("---"):
            output.append(stripped + "\n", style="bold")
        elif line.startswith("@@"):
            output.append(stripped + "\n", style="cyan")
        elif line.startswith("+"):
            output.append(stripped + "\n", style="green")
        elif line.startswith("-"):
            output.append(stripped + "\n", style="red")
        else:
            output.append(stripped + "\n", style="dim")

    summary = f"+{diff.additions} -{diff.deletions}"
    panel = Panel(
        output,
        title="[bold]Changes[/bold]",
        subtitle=summary,
        border_style="yellow",
        expand=True,
    )
    console.print(panel)


def render_stats(console: Console, diff: DiffResult) -> None:
    """Render a compact summary of diff statistics."""
    parts: list[str] = []
    if diff.additions:
        parts.append(f"[green]+{diff.additions}[/green]")
    if diff.deletions:
        parts.append(f"[red]-{diff.deletions}[/red]")
    if parts:
        console.print(" ".join(parts))
