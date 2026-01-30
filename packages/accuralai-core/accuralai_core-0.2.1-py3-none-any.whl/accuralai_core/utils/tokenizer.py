"""Simple token counting utilities for request/response usage metrics."""

from __future__ import annotations

import re
from collections.abc import Iterable, Mapping
from typing import Protocol

from ..contracts.models import GenerateRequest, GenerateResponse

# Basic pattern that splits words and keeps punctuation as individual tokens.
_TOKEN_PATTERN = re.compile(r"\w+|[^\w\s]", re.UNICODE)


class Tokenizer(Protocol):
    """Protocol describing the token counting helpers used by the pipeline."""

    def count_request_tokens(self, request: GenerateRequest) -> int:
        """Return the number of tokens contributed by the request payload."""

    def count_response_tokens(self, response: GenerateResponse) -> int:
        """Return the number of tokens contained in the response payload."""


class SimpleTokenizer:
    """Lightweight tokenizer approximating token counts via a regex split."""

    name = "simple"

    def count_request_tokens(self, request: GenerateRequest) -> int:  # noqa: D401
        parts: Iterable[str] = self._iter_request_text(request)
        return sum(self._count_text_tokens(part) for part in parts)

    def count_response_tokens(self, response: GenerateResponse) -> int:  # noqa: D401
        return self._count_text_tokens(response.output_text)

    def _iter_request_text(self, request: GenerateRequest) -> Iterable[str]:
        if request.system_prompt:
            yield request.system_prompt
        yield request.prompt
        for entry in request.history:
            for value in entry.values():
                yield from self._extract_text(value)

    def _extract_text(self, value: object) -> Iterable[str]:
        if isinstance(value, str):
            yield value
            return

        if isinstance(value, Mapping):
            for item in value.values():
                yield from self._extract_text(item)
            return

        if isinstance(value, Iterable) and not isinstance(value, (bytes, bytearray)):
            for item in value:
                yield from self._extract_text(item)

    def _count_text_tokens(self, text: str | None) -> int:
        if not text:
            return 0
        return len(_TOKEN_PATTERN.findall(text))


DEFAULT_TOKENIZER = SimpleTokenizer()

__all__ = ["Tokenizer", "SimpleTokenizer", "DEFAULT_TOKENIZER"]
