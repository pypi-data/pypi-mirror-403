"""File reader service."""

import logging
from pathlib import Path
from typing import Optional

from namespaces.base.config import load_yaml_config
from namespaces.files.handlers.csv.reader import CSVReader
from namespaces.files.handlers.pdf.reader import PDFReader
from namespaces.files.handlers.xlsx.reader import XLSXReader
from namespaces.files.models import FileReadRequest, FileReadResponse

logger = logging.getLogger(__name__)


class FileReaderService:
    """Coordinates file reading with pagination."""

    def __init__(self):
        config = load_yaml_config("files")
        reader_config = config["reader"]
        self.max_lines = reader_config["max_lines"]
        self.default_start = reader_config["default_start"]
        self.default_end = reader_config["default_end"]
        self._readers = {
            "csv": CSVReader(config["csv"], self.max_lines),
            "xlsx": XLSXReader(config["xlsx"], self.max_lines),
            "pdf": PDFReader(config["pdf"], self.max_lines),
        }

    async def read_file(self, request: FileReadRequest) -> FileReadResponse:
        """Read a file with pagination based on its type."""
        path = Path(request.path).resolve()
        file_type = path.suffix.lstrip(".").lower()
        reader = self._readers[file_type]

        content, total_lines, truncated = reader.read(path, request.start, request.end)

        return FileReadResponse(
            path=str(path),
            file_type=file_type,
            start=request.start,
            end=min(request.end, total_lines),
            total_lines=total_lines,
            output=content,
            truncated=truncated,
            summary=None,
        )


_filereader_service: Optional[FileReaderService] = None


def get_filereader_service() -> FileReaderService:
    """Get or create the singleton service instance."""
    global _filereader_service
    if _filereader_service is None:
        _filereader_service = FileReaderService()
    return _filereader_service
