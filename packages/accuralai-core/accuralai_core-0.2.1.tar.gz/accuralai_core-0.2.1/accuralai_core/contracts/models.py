"""Pydantic models shared across the AccuralAI ecosystem."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, model_validator


class Usage(BaseModel):
    """Token accounting information returned by a backend."""

    model_config = ConfigDict(extra="allow")

    prompt_tokens: int = Field(default=0, ge=0)
    completion_tokens: int = Field(default=0, ge=0)
    total_tokens: int = Field(default=0, ge=0)
    extra: Dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def _compute_total_tokens(cls, usage: "Usage") -> "Usage":
        """Ensure total tokens align with prompt + completion when not provided."""
        if usage.total_tokens == 0:
            usage.total_tokens = usage.prompt_tokens + usage.completion_tokens
        return usage


class GenerateRequest(BaseModel):
    """Canonical representation of a text generation request."""

    model_config = ConfigDict(extra="allow")

    id: UUID = Field(default_factory=uuid4)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    prompt: str
    system_prompt: Optional[str] = None
    history: List[Dict[str, Any]] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    parameters: Dict[str, Any] = Field(default_factory=dict)
    cache_key: Optional[str] = None
    route_hint: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    tools: List[Dict[str, Any]] = Field(default_factory=list)

    @model_validator(mode="after")
    def _validate_prompt(cls, request: "GenerateRequest") -> "GenerateRequest":
        """Guarantee prompts are provided."""
        if not request.prompt or not request.prompt.strip():
            if not request.history:
                msg = "GenerateRequest.prompt must be a non-empty string"
                raise ValueError(msg)
        return request


class GenerateResponse(BaseModel):
    """Canonical representation of a text generation response."""

    model_config = ConfigDict(extra="allow")

    id: UUID
    request_id: UUID
    output_text: str
    finish_reason: Literal["stop", "length", "content_filter", "error"]
    usage: Usage
    latency_ms: int = Field(ge=0)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    validator_events: List[Dict[str, Any]] = Field(default_factory=list)

    @model_validator(mode="after")
    def _ensure_response_text(cls, response: "GenerateResponse") -> "GenerateResponse":
        """Ensure responses contain text unless finish reason is error."""
        if response.finish_reason != "error" and not response.output_text:
            msg = "GenerateResponse.output_text cannot be empty when finish_reason is not 'error'"
            raise ValueError(msg)
        return response
