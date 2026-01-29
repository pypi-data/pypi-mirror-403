"""Pydantic models for terminal tool inputs/outputs."""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field

from namespaces.base.models import BaseRequest, BaseResponse


class TerminalExecuteRequest(BaseRequest):
    """Request to execute a terminal command."""

    command: str = Field(..., description="Shell command to execute")
    description: Optional[str] = Field(
        None,
        description="One sentence description of what this command does.",
    )
    timeout_seconds: int = Field(
        300,
        description="Command timeout in seconds (default: 300)",
        ge=1,
        le=3600,
    )


class TerminalExecuteResponse(BaseResponse):
    """Response from terminal command execution."""

    exit_code: Optional[int] = Field(
        None,
        description="Exit code from the command process.",
    )


class GlobRequest(BaseModel):
    """Request to find files matching a glob pattern."""

    pattern: str = Field(..., description="Glob pattern to match files (e.g., '**/*.py')")
    path: Optional[str] = Field(
        None,
        description="Base directory to search in. Defaults to current working directory.",
    )


class GlobResponse(BaseModel):
    """Response from glob file search."""

    files: list[str] = Field(
        default_factory=list,
        description="List of file paths matching the pattern.",
    )
    count: int = Field(0, description="Number of files found.")
    error: Optional[str] = Field(None, description="Error message if search failed.")


class GrepRequest(BaseModel):
    """Request to search file contents using regex."""

    pattern: str = Field(..., description="Regex pattern to search for.")
    path: Optional[str] = Field(
        None,
        description="File or directory to search in. Defaults to current working directory.",
    )
    glob: Optional[str] = Field(
        None,
        description="Glob pattern to filter files (e.g., '*.py').",
    )
    case_insensitive: bool = Field(
        False,
        description="Perform case-insensitive search.",
    )
    context_lines: int = Field(
        0,
        description="Number of context lines before and after each match.",
        ge=0,
        le=10,
    )
    max_results: int = Field(
        100,
        description="Maximum number of matches to return.",
        ge=1,
        le=1000,
    )


class GrepMatch(BaseModel):
    """Single grep match result."""

    file: str = Field(..., description="File path containing the match.")
    line_number: int = Field(..., description="Line number of the match.")
    line: str = Field(..., description="Content of the matching line.")
    context_before: list[str] = Field(
        default_factory=list,
        description="Lines before the match.",
    )
    context_after: list[str] = Field(
        default_factory=list,
        description="Lines after the match.",
    )


class GrepResponse(BaseModel):
    """Response from grep content search."""

    matches: list[GrepMatch] = Field(
        default_factory=list,
        description="List of matches found.",
    )
    count: int = Field(0, description="Total number of matches found.")
    truncated: bool = Field(
        False,
        description="True if results were truncated due to max_results limit.",
    )
    error: Optional[str] = Field(None, description="Error message if search failed.")
