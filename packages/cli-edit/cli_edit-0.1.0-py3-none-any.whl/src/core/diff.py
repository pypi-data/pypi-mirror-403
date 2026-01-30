"""Diff generation and analysis."""

from __future__ import annotations

import difflib
from typing import TYPE_CHECKING

from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from pathlib import Path


class DiffResult(BaseModel):
    """Result of a diff operation."""

    original: str
    modified: str
    unified_diff: str
    additions: int = Field(default=0)
    deletions: int = Field(default=0)
    has_changes: bool = Field(default=False)


def generate_diff(
    original: str,
    modified: str,
    filepath: Path,
    context_lines: int = 3,
) -> DiffResult:
    """Generate a unified diff between original and modified content."""
    original_lines = original.splitlines(keepends=True)
    modified_lines = modified.splitlines(keepends=True)

    if original_lines and not original_lines[-1].endswith("\n"):
        original_lines[-1] += "\n"
    if modified_lines and not modified_lines[-1].endswith("\n"):
        modified_lines[-1] += "\n"

    diff_lines = list(
        difflib.unified_diff(
            original_lines,
            modified_lines,
            fromfile=f"a/{filepath.name}",
            tofile=f"b/{filepath.name}",
            n=context_lines,
        )
    )

    additions = sum(1 for line in diff_lines if line.startswith("+") and not line.startswith("+++"))
    deletions = sum(1 for line in diff_lines if line.startswith("-") and not line.startswith("---"))
    unified = "".join(diff_lines)

    return DiffResult(
        original=original,
        modified=modified,
        unified_diff=unified,
        additions=additions,
        deletions=deletions,
        has_changes=bool(diff_lines),
    )


def apply_diff(original: str, modified: str) -> str:
    """Apply changes by returning the modified content.

    This is a simple passthrough since we already have the full modified content.
    """
    return modified
