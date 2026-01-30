"""Helpers for generating and validating identifiers."""

from __future__ import annotations

from typing import Union
from uuid import UUID, uuid4


def generate_trace_id() -> str:
    """Return a new trace identifier."""
    return uuid4().hex


def ensure_uuid(value: Union[str, UUID]) -> UUID:
    """Ensure the given value is a UUID instance."""
    if isinstance(value, UUID):
        return value
    return UUID(str(value))
