"""FastAPI router for file tools."""

from fastapi import APIRouter

from namespaces.files.models import (
    FileReadRequest,
    FileReadResponse,
    FileSummaryRequest,
    FileSummaryResponse,
)
from namespaces.files.reader import get_filereader_service
from namespaces.files.summarizer import get_filesummarizer_service

router = APIRouter()


@router.post(
    "/summarize",
    name="summarize",
    operation_id="files-summarize-file",
    summary="Summarize a file without reading its full content.",
    description="Analyze a file and return a summary of its structure and content.",
)
async def summarize_file(request: FileSummaryRequest) -> FileSummaryResponse:
    """Summarize file content based on file type."""
    service = get_filesummarizer_service()
    return await service.summarize_file(request)


@router.post(
    "/read",
    name="read",
    operation_id="files-read-file",
    summary="Read a portion of a file with pagination.",
    description="Read specific rows/pages from a file. For CSV/XLSX: rows are 0-indexed. For PDF: pages are 0-indexed. For multi-sheet XLSX, rows are sequential across sheets.",
)
async def read_file(request: FileReadRequest) -> FileReadResponse:
    """Read file content with pagination based on file type."""
    service = get_filereader_service()
    return await service.read_file(request)
