"""Anthropic Claude AI provider integration."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import anthropic

from src.ai.base import (
    AIProvider,
    EditRequest,
    EditResponse,
    build_system_prompt,
    build_user_prompt,
)

if TYPE_CHECKING:
    from collections.abc import Iterator

logger = logging.getLogger(__name__)


class ClaudeProvider(AIProvider):
    """Anthropic Claude code editing provider."""

    def __init__(self, api_key: str, model: str = "claude-sonnet-4-20250514") -> None:
        self._api_key = api_key
        self._model = model
        self._client: anthropic.Anthropic | None = None

    def _get_client(self) -> anthropic.Anthropic:
        """Lazily initialize the Anthropic client."""
        if self._client is None:
            self._client = anthropic.Anthropic(api_key=self._api_key)
        return self._client

    def edit(self, request: EditRequest) -> EditResponse:
        """Send an edit request and return the complete response."""
        client = self._get_client()
        user_msg = build_user_prompt(request)

        try:
            message = client.messages.create(
                model=self._model,
                max_tokens=8192,
                system=build_system_prompt(),
                messages=[{"role": "user", "content": user_msg}],
            )
        except anthropic.AuthenticationError as exc:
            raise RuntimeError(
                "Invalid Anthropic API key. Set ANTHROPIC_API_KEY in your environment."
            ) from exc
        except anthropic.RateLimitError as exc:
            raise RuntimeError(
                "Anthropic rate limit hit. Wait a moment and try again."
            ) from exc
        except anthropic.APIError as exc:
            raise RuntimeError(f"Anthropic API error: {exc}") from exc

        content = ""
        for block in message.content:
            if block.type == "text":
                content += block.text

        tokens = 0
        if message.usage:
            tokens = message.usage.input_tokens + message.usage.output_tokens

        return EditResponse(
            edited_content=content,
            tokens_used=tokens,
        )

    def edit_stream(self, request: EditRequest) -> Iterator[str]:
        """Stream the edited content from Claude."""
        client = self._get_client()
        user_msg = build_user_prompt(request)

        try:
            with client.messages.stream(
                model=self._model,
                max_tokens=8192,
                system=build_system_prompt(),
                messages=[{"role": "user", "content": user_msg}],
            ) as stream:
                yield from stream.text_stream
        except anthropic.AuthenticationError as exc:
            raise RuntimeError(
                "Invalid Anthropic API key. Set ANTHROPIC_API_KEY in your environment."
            ) from exc
        except anthropic.RateLimitError as exc:
            raise RuntimeError(
                "Anthropic rate limit hit. Wait a moment and try again."
            ) from exc
        except anthropic.APIError as exc:
            raise RuntimeError(f"Anthropic API error: {exc}") from exc

    def is_available(self) -> bool:
        """Check if the Anthropic API key is configured."""
        return bool(self._api_key)
