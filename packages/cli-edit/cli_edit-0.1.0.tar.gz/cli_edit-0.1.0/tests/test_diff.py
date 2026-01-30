"""Tests for diff generation."""

from __future__ import annotations

from pathlib import Path

from src.core.diff import DiffResult, generate_diff


class TestGenerateDiff:
    """Tests for unified diff generation."""

    def test_no_changes(self) -> None:
        content = "line1\nline2\n"
        diff = generate_diff(content, content, Path("test.py"))
        assert not diff.has_changes
        assert diff.additions == 0
        assert diff.deletions == 0

    def test_addition(self) -> None:
        original = "line1\nline2\n"
        modified = "line1\nline2\nline3\n"
        diff = generate_diff(original, modified, Path("test.py"))
        assert diff.has_changes
        assert diff.additions == 1
        assert diff.deletions == 0
        assert "+line3" in diff.unified_diff

    def test_deletion(self) -> None:
        original = "line1\nline2\nline3\n"
        modified = "line1\nline3\n"
        diff = generate_diff(original, modified, Path("test.py"))
        assert diff.has_changes
        assert diff.deletions == 1
        assert "-line2" in diff.unified_diff

    def test_modification(self) -> None:
        original = "line1\nline2\n"
        modified = "line1\nline2_modified\n"
        diff = generate_diff(original, modified, Path("test.py"))
        assert diff.has_changes
        assert diff.additions == 1
        assert diff.deletions == 1

    def test_context_lines(self) -> None:
        original = "a\nb\nc\nd\ne\nf\ng\n"
        modified = "a\nb\nc\nD\ne\nf\ng\n"
        diff = generate_diff(original, modified, Path("test.py"), context_lines=1)
        assert diff.has_changes
        lines = diff.unified_diff.splitlines()
        context_count = sum(
            1 for line in lines
            if line and not line.startswith(("@@", "---", "+++", "+", "-"))
        )
        assert context_count <= 2

    def test_empty_original(self) -> None:
        diff = generate_diff("", "new content\n", Path("test.py"))
        assert diff.has_changes
        assert diff.additions >= 1

    def test_empty_modified(self) -> None:
        diff = generate_diff("old content\n", "", Path("test.py"))
        assert diff.has_changes
        assert diff.deletions >= 1

    def test_file_header(self) -> None:
        diff = generate_diff("old\n", "new\n", Path("main.py"))
        assert "a/main.py" in diff.unified_diff
        assert "b/main.py" in diff.unified_diff


class TestDiffResult:
    """Tests for DiffResult model."""

    def test_model_creation(self) -> None:
        result = DiffResult(
            original="old",
            modified="new",
            unified_diff="diff content",
            additions=1,
            deletions=1,
            has_changes=True,
        )
        assert result.additions == 1
        assert result.has_changes is True
