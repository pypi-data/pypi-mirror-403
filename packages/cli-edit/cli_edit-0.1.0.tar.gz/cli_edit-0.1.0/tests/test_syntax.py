"""Tests for syntax highlighting utilities."""

from __future__ import annotations

from pathlib import Path

from pygments.lexers import PythonLexer, TextLexer

from src.utils.syntax import get_language_name, get_lexer, highlight_code


class TestGetLexer:
    """Tests for lexer detection."""

    def test_python_file(self) -> None:
        lexer = get_lexer(Path("test.py"))
        assert isinstance(lexer, PythonLexer)

    def test_unknown_extension(self) -> None:
        lexer = get_lexer(Path("file.xyzabc"))
        assert isinstance(lexer, TextLexer)


class TestHighlightCode:
    """Tests for code highlighting."""

    def test_returns_string(self) -> None:
        result = highlight_code("x = 1", Path("test.py"))
        assert isinstance(result, str)
        assert len(result) > 0

    def test_plain_text_fallback(self) -> None:
        result = highlight_code("hello world", Path("file.unknown"))
        assert isinstance(result, str)


class TestGetLanguageName:
    """Tests for language name detection."""

    def test_python(self) -> None:
        assert get_language_name(Path("test.py")) == "Python"

    def test_javascript(self) -> None:
        name = get_language_name(Path("app.js"))
        assert "JavaScript" in name or "javascript" in name.lower()

    def test_unknown(self) -> None:
        assert get_language_name(Path("file.xyzabc")) == "Plain Text"
