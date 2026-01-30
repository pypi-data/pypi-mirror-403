"""Tests for UI components."""

from __future__ import annotations

from io import StringIO
from pathlib import Path

from rich.console import Console

from src.core.diff import DiffResult
from src.ui.diff_view import render_diff, render_stats
from src.ui.display import display_error, display_file, display_info, display_status


def _make_console(*, highlight: bool = True) -> Console:
    """Create a console that captures output."""
    return Console(file=StringIO(), force_terminal=True, width=120, highlight=highlight)


def _make_plain_console() -> Console:
    """Create a console with no markup or color for plain text assertions."""
    return Console(file=StringIO(), no_color=True, width=120, highlight=False)


def _get_output(console: Console) -> str:
    """Get captured output from console."""
    file = console.file
    assert isinstance(file, StringIO)
    return file.getvalue()


class TestDisplayFile:
    """Tests for file display."""

    def test_display_python_file(self) -> None:
        console = _make_console()
        display_file(console, "x = 1\n", Path("test.py"))
        output = _get_output(console)
        assert "test.py" in output

    def test_display_with_line_count(self) -> None:
        console = _make_console()
        display_file(console, "line1\nline2\nline3\n", Path("test.py"))
        output = _get_output(console)
        assert "3 lines" in output


class TestDisplayMessages:
    """Tests for status/error/info display."""

    def test_display_status(self) -> None:
        console = _make_console()
        display_status(console, "Saved!")
        output = _get_output(console)
        assert "Saved!" in output

    def test_display_error(self) -> None:
        console = _make_console()
        display_error(console, "Something broke")
        output = _get_output(console)
        assert "Something broke" in output

    def test_display_info(self) -> None:
        console = _make_console()
        display_info(console, "FYI")
        output = _get_output(console)
        assert "FYI" in output


class TestDiffView:
    """Tests for diff rendering."""

    def test_render_no_changes(self) -> None:
        console = _make_console()
        diff = DiffResult(
            original="x", modified="x", unified_diff="", has_changes=False,
        )
        render_diff(console, diff)
        output = _get_output(console)
        assert "No changes" in output

    def test_render_with_changes(self) -> None:
        console = _make_plain_console()
        diff = DiffResult(
            original="old\n",
            modified="new\n",
            unified_diff="--- a/test.py\n+++ b/test.py\n@@ -1 +1 @@\n-old\n+new\n",
            additions=1,
            deletions=1,
            has_changes=True,
        )
        render_diff(console, diff)
        output = _get_output(console)
        assert "+1" in output
        assert "-1" in output

    def test_render_stats(self) -> None:
        console = _make_plain_console()
        diff = DiffResult(
            original="", modified="new\n",
            unified_diff="+new", additions=3, deletions=1, has_changes=True,
        )
        render_stats(console, diff)
        output = _get_output(console)
        assert "+3" in output
        assert "-1" in output
