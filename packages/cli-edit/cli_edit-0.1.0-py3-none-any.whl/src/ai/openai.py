"""OpenAI API provider integration."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import openai

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


class OpenAIProvider(AIProvider):
    """OpenAI code editing provider."""

    def __init__(self, api_key: str, model: str = "gpt-4o") -> None:
        self._api_key = api_key
        self._model = model
        self._client: openai.OpenAI | None = None

    def _get_client(self) -> openai.OpenAI:
        """Lazily initialize the OpenAI client."""
        if self._client is None:
            self._client = openai.OpenAI(api_key=self._api_key)
        return self._client

    def edit(self, request: EditRequest) -> EditResponse:
        """Send an edit request and return the complete response."""
        client = self._get_client()
        user_msg = build_user_prompt(request)

        try:
            response = client.chat.completions.create(
                model=self._model,
                messages=[
                    {"role": "system", "content": build_system_prompt()},
                    {"role": "user", "content": user_msg},
                ],
                max_tokens=8192,
                temperature=0.0,
            )
        except openai.AuthenticationError as exc:
            raise RuntimeError(
                "Invalid OpenAI API key. Set OPENAI_API_KEY in your environment."
            ) from exc
        except openai.RateLimitError as exc:
            raise RuntimeError(
                "OpenAI rate limit hit. Wait a moment and try again."
            ) from exc
        except openai.APIError as exc:
            raise RuntimeError(f"OpenAI API error: {exc}") from exc

        choice = response.choices[0]
        content = choice.message.content or ""

        tokens = 0
        if response.usage:
            tokens = response.usage.total_tokens

        return EditResponse(
            edited_content=content,
            tokens_used=tokens,
        )

    def edit_stream(self, request: EditRequest) -> Iterator[str]:
        """Stream the edited content from OpenAI."""
        client = self._get_client()
        user_msg = build_user_prompt(request)

        try:
            stream = client.chat.completions.create(
                model=self._model,
                messages=[
                    {"role": "system", "content": build_system_prompt()},
                    {"role": "user", "content": user_msg},
                ],
                max_tokens=8192,
                temperature=0.0,
                stream=True,
            )
            for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        except openai.AuthenticationError as exc:
            raise RuntimeError(
                "Invalid OpenAI API key. Set OPENAI_API_KEY in your environment."
            ) from exc
        except openai.RateLimitError as exc:
            raise RuntimeError(
                "OpenAI rate limit hit. Wait a moment and try again."
            ) from exc
        except openai.APIError as exc:
            raise RuntimeError(f"OpenAI API error: {exc}") from exc

    def is_available(self) -> bool:
        """Check if the OpenAI API key is configured."""
        return bool(self._api_key)
