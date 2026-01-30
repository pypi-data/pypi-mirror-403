"""Tests for the CLI entry point."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import patch

if TYPE_CHECKING:
    from pathlib import Path

from click.testing import CliRunner

from src.cli.main import app


class TestCLI:
    """Tests for CLI commands."""

    def test_help(self) -> None:
        runner = CliRunner()
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "AI-powered edits" in result.output

    def test_version(self) -> None:
        runner = CliRunner()
        result = runner.invoke(app, ["--version"])
        assert result.exit_code == 0
        assert "0.1.0" in result.output

    def test_nonexistent_file(self) -> None:
        runner = CliRunner()
        result = runner.invoke(app, ["/nonexistent/path/file.py"])
        assert result.exit_code != 0

    def test_missing_api_key(self, tmp_path: Path) -> None:
        f = tmp_path / "test.py"
        f.write_text("x = 1\n")

        runner = CliRunner()
        with patch.dict("os.environ", {}, clear=True):
            result = runner.invoke(app, [str(f)])
        assert result.exit_code != 0
