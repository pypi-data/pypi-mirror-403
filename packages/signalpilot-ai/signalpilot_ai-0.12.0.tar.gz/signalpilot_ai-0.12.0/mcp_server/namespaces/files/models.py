"""Pydantic models for file reader tool inputs/outputs."""

from pydantic import BaseModel, Field

from namespaces.base.models import BaseRequest, BaseResponse


class FileSummaryRequest(BaseRequest):
    """Request to summarize a file."""

    path: str = Field(..., description="Absolute or relative path to the file.")


class FileSummaryResponse(BaseResponse):
    """Response from file summarization."""

    path: str = Field(..., description="Path to the file that was summarized.")
    file_type: str = Field(..., description="Detected file type.")


class FileReadRequest(BaseRequest):
    """Request to read a file with pagination."""

    path: str = Field(..., description="Absolute or relative path to the file.")
    start: int = Field(0, description="Start line/row/page number (0-indexed).")
    end: int = Field(100, description="End line/row/page number (exclusive).")


class FileReadResponse(BaseResponse):
    """Response from file reading - raw content only, no AI summary."""

    path: str = Field(..., description="Path to the file that was read.")
    file_type: str = Field(..., description="Detected file type.")
    start: int = Field(..., description="Start position that was read.")
    end: int = Field(..., description="End position that was read.")
    total_lines: int = Field(
        ..., description="Total number of lines/rows/pages in the file."
    )
