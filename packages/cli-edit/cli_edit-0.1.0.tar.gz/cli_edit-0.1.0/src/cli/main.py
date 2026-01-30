"""CLI entry point for cli-edit."""

from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import TYPE_CHECKING

import click
from rich.console import Console

from src.ai.claude import ClaudeProvider
from src.ai.openai import OpenAIProvider
from src.core.editor import Editor
from src.core.file_handler import FileError
from src.ui.display import display_error, display_info
from src.utils.config import Config, load_config, resolve_model

if TYPE_CHECKING:
    from src.ai.base import AIProvider

logger = logging.getLogger(__name__)

BANNER = """[bold blue]cli-edit[/bold blue] [dim]- AI code editor for terminals[/dim]"""


def _setup_logging(verbose: bool) -> None:
    """Configure logging based on verbosity."""
    level = logging.DEBUG if verbose else logging.WARNING
    logging.basicConfig(
        level=level,
        format="%(name)s %(levelname)s: %(message)s",
    )


def _create_provider(config: Config) -> AIProvider:
    """Create the appropriate AI provider based on configuration."""
    model_id, provider_name = resolve_model(config.model)

    if provider_name == "anthropic":
        if not config.anthropic_api_key:
            raise click.ClickException(
                "Anthropic API key required. Set ANTHROPIC_API_KEY environment variable "
                "or add anthropic_api_key to your config file."
            )
        return ClaudeProvider(api_key=config.anthropic_api_key, model=model_id)

    if not config.openai_api_key:
        raise click.ClickException(
            "OpenAI API key required. Set OPENAI_API_KEY environment variable "
            "or add openai_api_key to your config file."
        )
    return OpenAIProvider(api_key=config.openai_api_key, model=model_id)


@click.command()
@click.argument("file", type=click.Path(exists=True))
@click.option(
    "--model", "-m",
    default=None,
    help="AI model to use (e.g., claude-sonnet, gpt-4o).",
)
@click.option(
    "--prompt", "-p",
    default=None,
    help="Edit prompt (skips interactive prompt).",
)
@click.option(
    "--yes", "-y",
    is_flag=True,
    default=False,
    help="Auto-accept changes (non-interactive mode).",
)
@click.option(
    "--no-backup",
    is_flag=True,
    default=False,
    help="Skip creating a backup file.",
)
@click.option(
    "--context-lines", "-c",
    default=None,
    type=int,
    help="Number of context lines in diff.",
)
@click.option(
    "--theme", "-t",
    default=None,
    help="Syntax highlighting theme.",
)
@click.option(
    "--no-stream",
    is_flag=True,
    default=False,
    help="Disable response streaming.",
)
@click.option(
    "--verbose", "-v",
    is_flag=True,
    default=False,
    help="Enable debug logging.",
)
@click.version_option(version="0.1.0", prog_name="cli-edit")
def app(
    file: str,
    model: str | None,
    prompt: str | None,
    yes: bool,
    no_backup: bool,
    context_lines: int | None,
    theme: str | None,
    no_stream: bool,
    verbose: bool,
) -> None:
    """Open a file and make AI-powered edits from the terminal.

    Describe changes in natural language, preview the diff, then accept or reject.
    """
    _setup_logging(verbose)
    console = Console()

    try:
        config = load_config()
    except Exception as exc:
        display_error(console, f"Failed to load config: {exc}")
        sys.exit(1)

    if model is not None:
        config.model = model
    if no_backup:
        config.backup_enabled = False
    if context_lines is not None:
        config.context_lines = context_lines
    if theme is not None:
        config.theme = theme
    if no_stream:
        config.streaming = False

    console.print(BANNER)
    console.print()

    try:
        provider = _create_provider(config)
    except click.ClickException as exc:
        display_error(console, str(exc.message))
        sys.exit(1)

    filepath = Path(file).resolve()
    editor = Editor(console=console, provider=provider, config=config)

    try:
        editor.open_file(filepath)
    except FileError as exc:
        display_error(console, str(exc))
        sys.exit(1)

    try:
        if prompt and yes:
            success = editor.run_noninteractive(prompt)
            sys.exit(0 if success else 1)
        else:
            editor.run_interactive(initial_prompt=prompt or "")
    except KeyboardInterrupt:
        console.print()
        display_info(console, "Interrupted. Exiting.")
        sys.exit(130)


if __name__ == "__main__":
    app()
