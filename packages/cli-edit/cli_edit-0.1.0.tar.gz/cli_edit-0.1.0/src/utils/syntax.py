"""Syntax highlighting utilities."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from pygments import highlight
from pygments.formatters import TerminalTrueColorFormatter
from pygments.lexers import TextLexer, get_lexer_for_filename
from pygments.util import ClassNotFound

if TYPE_CHECKING:
    from pathlib import Path

    from pygments.lexer import Lexer

logger = logging.getLogger(__name__)


def get_lexer(filepath: Path) -> Lexer:
    """Get the appropriate Pygments lexer for a file.

    Falls back to plain text if no lexer is found.
    """
    try:
        return get_lexer_for_filename(str(filepath))
    except ClassNotFound:
        logger.debug("No lexer found for %s, using plain text", filepath)
        return TextLexer()  # type: ignore[no-any-return]


def highlight_code(code: str, filepath: Path, theme: str = "monokai") -> str:
    """Apply syntax highlighting to code.

    Returns the highlighted string with ANSI escape codes.
    """
    lexer = get_lexer(filepath)
    formatter = TerminalTrueColorFormatter(style=theme)
    result: str = highlight(code, lexer, formatter)
    return result


def get_language_name(filepath: Path) -> str:
    """Get the human-readable language name for a file."""
    try:
        lexer = get_lexer_for_filename(str(filepath))
        return str(lexer.name)  # type: ignore[attr-defined]
    except ClassNotFound:
        return "Plain Text"
