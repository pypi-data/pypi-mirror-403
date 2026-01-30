"""Tests for file handling."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from pathlib import Path

from src.core.file_handler import (
    FileError,
    create_backup,
    read_file,
    restore_backup,
    write_file,
)


class TestReadFile:
    """Tests for reading files."""

    def test_read_utf8_file(self, tmp_path: Path) -> None:
        f = tmp_path / "test.py"
        f.write_text("print('hello')\n", encoding="utf-8")

        info = read_file(f)
        assert info.content == "print('hello')\n"
        assert info.encoding == "utf-8"
        assert info.line_ending == "\n"

    def test_read_crlf_file(self, tmp_path: Path) -> None:
        f = tmp_path / "test.py"
        f.write_bytes(b"line1\r\nline2\r\n")

        info = read_file(f)
        assert info.content == "line1\nline2\n"
        assert info.line_ending == "\r\n"

    def test_read_latin1_file(self, tmp_path: Path) -> None:
        f = tmp_path / "test.txt"
        f.write_bytes("caf\xe9\n".encode("latin-1"))

        info = read_file(f)
        assert "caf" in info.content

    def test_nonexistent_file_raises(self, tmp_path: Path) -> None:
        with pytest.raises(FileError, match="not found"):
            read_file(tmp_path / "missing.py")

    def test_directory_raises(self, tmp_path: Path) -> None:
        with pytest.raises(FileError, match="Not a file"):
            read_file(tmp_path)

    def test_too_large_file_raises(self, tmp_path: Path) -> None:
        f = tmp_path / "big.txt"
        f.write_bytes(b"x" * (2 * 1024 * 1024))

        with pytest.raises(FileError, match="too large"):
            read_file(f, max_size_mb=1)

    def test_empty_file(self, tmp_path: Path) -> None:
        f = tmp_path / "empty.py"
        f.write_text("")

        info = read_file(f)
        assert info.content == ""


class TestWriteFile:
    """Tests for writing files."""

    def test_write_preserves_lf(self, tmp_path: Path) -> None:
        f = tmp_path / "test.py"
        f.write_text("original\n")

        info = read_file(f)
        write_file(info, "modified\n")

        assert f.read_text() == "modified\n"

    def test_write_preserves_crlf(self, tmp_path: Path) -> None:
        f = tmp_path / "test.py"
        f.write_bytes(b"original\r\n")

        info = read_file(f)
        write_file(info, "modified\n")

        assert f.read_bytes() == b"modified\r\n"

    def test_atomic_write_on_error(self, tmp_path: Path) -> None:
        f = tmp_path / "test.py"
        f.write_text("original\n")

        info = read_file(f)
        write_file(info, "new content\n")

        assert f.read_text() == "new content\n"


class TestBackup:
    """Tests for backup creation and restoration."""

    def test_create_backup(self, tmp_path: Path) -> None:
        f = tmp_path / "test.py"
        f.write_text("content\n")

        info = read_file(f)
        backup = create_backup(info)

        assert backup.exists()
        assert backup.read_text() == "content\n"
        assert backup.name == "test.py.bak"

    def test_backup_with_existing(self, tmp_path: Path) -> None:
        f = tmp_path / "test.py"
        f.write_text("content\n")
        (tmp_path / "test.py.bak").write_text("old backup\n")

        info = read_file(f)
        backup = create_backup(info)

        assert backup.name == "test.py.bak.1"

    def test_restore_backup(self, tmp_path: Path) -> None:
        f = tmp_path / "test.py"
        f.write_text("original\n")

        info = read_file(f)
        backup = create_backup(info)

        f.write_text("modified\n")
        restore_backup(f, backup)

        assert f.read_text() == "original\n"

    def test_restore_missing_backup_raises(self, tmp_path: Path) -> None:
        with pytest.raises(FileError, match="Backup not found"):
            restore_backup(
                tmp_path / "test.py",
                tmp_path / "nonexistent.bak",
            )
