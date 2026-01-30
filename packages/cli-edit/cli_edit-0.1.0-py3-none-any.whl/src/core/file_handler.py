"""File reading, writing, and backup management."""

from __future__ import annotations

import logging
import os
import shutil
import tempfile
from pathlib import Path  # noqa: TC003 (needed at runtime by Pydantic)

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class FileInfo(BaseModel):
    """Metadata and content of a loaded file."""

    path: Path
    content: str
    encoding: str = Field(default="utf-8")
    line_ending: str = Field(default="\n")
    size_bytes: int = Field(default=0)

    model_config = {"arbitrary_types_allowed": True}


class FileError(Exception):
    """Raised for file operation failures."""


ENCODINGS_TO_TRY: list[str] = ["utf-8", "utf-8-sig", "latin-1", "cp1252", "ascii"]


def _detect_encoding(raw: bytes) -> str:
    """Detect file encoding by trying common encodings in order."""
    for enc in ENCODINGS_TO_TRY:
        try:
            raw.decode(enc)
            return enc
        except (UnicodeDecodeError, ValueError):
            continue
    return "utf-8"


def _detect_line_ending(raw: bytes) -> str:
    """Detect the dominant line ending style from raw bytes."""
    crlf_count = raw.count(b"\r\n")
    lf_count = raw.count(b"\n") - crlf_count
    if crlf_count > lf_count:
        return "\r\n"
    return "\n"


def read_file(path: Path, max_size_mb: int = 10) -> FileInfo:
    """Read a file with encoding detection and metadata extraction.

    Raises FileError on permission or size issues.
    """
    resolved = path.resolve()

    if not resolved.exists():
        raise FileError(f"File not found: {resolved}")

    if not resolved.is_file():
        raise FileError(f"Not a file: {resolved}")

    if not os.access(resolved, os.R_OK):
        raise FileError(f"Permission denied: {resolved}")

    size = resolved.stat().st_size
    max_bytes = max_size_mb * 1024 * 1024
    if size > max_bytes:
        raise FileError(
            f"File too large: {size / 1024 / 1024:.1f}MB "
            f"(max {max_size_mb}MB)"
        )

    raw = resolved.read_bytes()
    encoding = _detect_encoding(raw)
    line_ending = _detect_line_ending(raw)
    content = raw.decode(encoding)

    if line_ending == "\r\n":
        content = content.replace("\r\n", "\n")

    return FileInfo(
        path=resolved,
        content=content,
        encoding=encoding,
        line_ending=line_ending,
        size_bytes=size,
    )


def write_file(file_info: FileInfo, new_content: str) -> None:
    """Write content to file atomically, preserving encoding and line endings.

    Writes to a temporary file first, then renames for atomicity.
    """
    output = new_content
    if file_info.line_ending == "\r\n":
        output = output.replace("\n", "\r\n")

    target = file_info.path
    parent = target.parent

    try:
        fd, tmp_path = tempfile.mkstemp(
            dir=parent,
            prefix=f".{target.name}.",
            suffix=".tmp",
        )
        try:
            with os.fdopen(fd, "w", encoding=file_info.encoding) as f:
                f.write(output)
            shutil.move(tmp_path, target)
        except Exception:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
            raise
    except PermissionError as exc:
        raise FileError(f"Permission denied writing to: {target}") from exc
    except OSError as exc:
        raise FileError(f"Failed to write file: {exc}") from exc


def create_backup(file_info: FileInfo) -> Path:
    """Create a backup of the file before modification.

    Returns the path to the backup file.
    """
    backup_path = file_info.path.with_suffix(file_info.path.suffix + ".bak")

    counter = 1
    while backup_path.exists():
        backup_path = file_info.path.with_suffix(
            f"{file_info.path.suffix}.bak.{counter}"
        )
        counter += 1

    try:
        shutil.copy2(file_info.path, backup_path)
        logger.info("Backup created: %s", backup_path)
        return backup_path
    except OSError as exc:
        raise FileError(f"Failed to create backup: {exc}") from exc


def restore_backup(original_path: Path, backup_path: Path) -> None:
    """Restore a file from its backup."""
    if not backup_path.exists():
        raise FileError(f"Backup not found: {backup_path}")
    try:
        shutil.copy2(backup_path, original_path)
        logger.info("Restored from backup: %s", backup_path)
    except OSError as exc:
        raise FileError(f"Failed to restore backup: {exc}") from exc
