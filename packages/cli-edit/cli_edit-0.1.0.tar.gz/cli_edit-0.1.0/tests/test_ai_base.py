"""Tests for AI base classes and utilities."""

from __future__ import annotations

from pathlib import Path

from src.ai.base import EditRequest, EditResponse, build_system_prompt, build_user_prompt


class TestEditRequest:
    """Tests for EditRequest model."""

    def test_creation(self) -> None:
        req = EditRequest(
            file_path=Path("test.py"),
            file_content="x = 1\n",
            prompt="add type hint",
        )
        assert req.file_path == Path("test.py")
        assert req.prompt == "add type hint"
        assert req.language == ""

    def test_with_language(self) -> None:
        req = EditRequest(
            file_path=Path("test.py"),
            file_content="x = 1\n",
            prompt="add type hint",
            language="Python",
        )
        assert req.language == "Python"


class TestEditResponse:
    """Tests for EditResponse model."""

    def test_creation(self) -> None:
        resp = EditResponse(edited_content="x: int = 1\n")
        assert resp.edited_content == "x: int = 1\n"
        assert resp.tokens_used == 0
        assert resp.explanation == ""


class TestPromptBuilding:
    """Tests for prompt construction."""

    def test_system_prompt(self) -> None:
        prompt = build_system_prompt()
        assert "code editor" in prompt.lower()
        assert "raw file content" in prompt.lower()

    def test_user_prompt_contains_file(self) -> None:
        req = EditRequest(
            file_path=Path("main.py"),
            file_content="print('hello')\n",
            prompt="add logging",
            language="Python",
        )
        msg = build_user_prompt(req)
        assert "main.py" in msg
        assert "Python" in msg
        assert "add logging" in msg
        assert "print('hello')" in msg
