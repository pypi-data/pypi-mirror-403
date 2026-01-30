"""File content display with syntax highlighting."""

from __future__ import annotations

from typing import TYPE_CHECKING

from rich.panel import Panel
from rich.syntax import Syntax
from rich.text import Text

from src.utils.syntax import get_language_name

if TYPE_CHECKING:
    from pathlib import Path

    from rich.console import Console


def display_file(
    console: Console,
    content: str,
    filepath: Path,
    theme: str = "monokai",
) -> None:
    """Display a file with syntax highlighting and line numbers."""
    language = get_language_name(filepath).lower()
    syntax = Syntax(
        content,
        language,
        theme=theme,
        line_numbers=True,
        word_wrap=False,
    )

    file_size = len(content.encode("utf-8"))
    line_count = content.count("\n") + (1 if content and not content.endswith("\n") else 0)

    subtitle = f"{language} | {line_count} lines | {_format_size(file_size)}"

    panel = Panel(
        syntax,
        title=f"[bold]{filepath.name}[/bold]",
        subtitle=subtitle,
        border_style="blue",
        expand=True,
    )
    console.print(panel)


def display_status(console: Console, message: str, style: str = "bold green") -> None:
    """Display a status message."""
    console.print(Text(message, style=style))


def display_error(console: Console, message: str) -> None:
    """Display an error message."""
    console.print(Text(f"Error: {message}", style="bold red"))


def display_info(console: Console, message: str) -> None:
    """Display an info message."""
    console.print(Text(message, style="dim"))


def _format_size(size_bytes: int) -> str:
    """Format byte size into human-readable string."""
    if size_bytes < 1024:
        return f"{size_bytes}B"
    if size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f}KB"
    return f"{size_bytes / (1024 * 1024):.1f}MB"
