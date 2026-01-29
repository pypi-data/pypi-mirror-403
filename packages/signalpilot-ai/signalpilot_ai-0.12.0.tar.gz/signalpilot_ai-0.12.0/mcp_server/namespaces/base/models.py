"""Base pydantic models for all namespace requests and responses."""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class BaseRequest(BaseModel):
    """Base request with common fields."""

    force_refresh: bool = Field(
        False,
        description="Force refresh LLM cache. Default is False.",
    )


class BaseResponse(BaseModel):
    """Base response with common output, truncation, and summary fields."""

    output: Optional[str] = Field(
        None, description="Tool output (truncated when large)."
    )
    truncated: bool = Field(
        False,
        description="True when output exceeded limits and was truncated.",
    )
    summary: Optional[str] = Field(
        None,
        description="Summary of the full output when truncation occurs.",
    )
