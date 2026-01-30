"""Abstract base class for AI provider integrations."""

from __future__ import annotations

import abc
from pathlib import Path  # noqa: TC003 (needed at runtime by Pydantic)
from typing import TYPE_CHECKING

from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from collections.abc import Iterator


class EditRequest(BaseModel):
    """Request payload sent to an AI provider."""

    file_path: Path
    file_content: str
    prompt: str
    language: str = Field(default="")

    model_config = {"arbitrary_types_allowed": True}


class EditResponse(BaseModel):
    """Response from an AI provider."""

    edited_content: str
    explanation: str = Field(default="")
    tokens_used: int = Field(default=0)


class AIProvider(abc.ABC):
    """Abstract base for AI code editing providers."""

    @abc.abstractmethod
    def edit(self, request: EditRequest) -> EditResponse:
        """Send an edit request and return the full response."""

    @abc.abstractmethod
    def edit_stream(self, request: EditRequest) -> Iterator[str]:
        """Send an edit request and stream the response content."""

    @abc.abstractmethod
    def is_available(self) -> bool:
        """Check if this provider is configured and reachable."""


def build_system_prompt() -> str:
    """Build the system prompt for code editing."""
    return (
        "You are a precise code editor. The user will provide a file and a request "
        "for changes. You must return ONLY the complete modified file content with "
        "the requested changes applied. Do not include any explanation, markdown "
        "formatting, code fences, or commentary. Return only the raw file content, "
        "nothing else. Preserve the original indentation style, line endings, and "
        "formatting conventions used in the file."
    )


def build_user_prompt(request: EditRequest) -> str:
    """Build the user message for the AI."""
    lang = request.language or "unknown"
    return (
        f"File: {request.file_path.name} ({lang})\n"
        f"Request: {request.prompt}\n\n"
        f"--- FILE CONTENT ---\n{request.file_content}\n--- END FILE ---"
    )
