"""File summarizer service."""

import logging
from pathlib import Path
from typing import Optional

from namespaces.base.config import load_yaml_config
from namespaces.base.output_processor import OutputProcessor
from namespaces.base.service import BaseService
from namespaces.files.handlers.csv.summarizer import CSVSummarizer
from namespaces.files.handlers.pdf.summarizer import PDFSummarizer
from namespaces.files.handlers.xlsx.summarizer import XLSXSummarizer
from namespaces.files.models import FileSummaryRequest, FileSummaryResponse

logger = logging.getLogger(__name__)


class FileSummarizerService(BaseService):
    """Coordinates file summarization."""

    def __init__(self) -> None:
        super().__init__("files")
        config = load_yaml_config("files")
        self._summarizers = {
            "csv": CSVSummarizer(config["csv"]),
            "xlsx": XLSXSummarizer(config["xlsx"]),
            "pdf": PDFSummarizer(config["pdf"]),
        }

    def _get_prompt_path(self) -> Path:
        """Return path to prompt.md in files namespace."""
        return Path(__file__).parent / self.prompt_file

    async def summarize_file(self, request: FileSummaryRequest) -> FileSummaryResponse:
        """Summarize a file based on its type."""
        path = Path(request.path).resolve()
        file_type = path.suffix.lstrip(".").lower()
        summarizer = self._summarizers[file_type]
        summary_text = summarizer.summarize(path)

        output, truncated, summary = await self._output_processor.process(
            query=f"summarize {path.name}",
            output=summary_text,
            prompt=self._system_prompt,
            force_refresh=request.force_refresh,
        )

        return FileSummaryResponse(
            path=str(path),
            file_type=file_type,
            output=output,
            truncated=truncated,
            summary=summary,
        )


_filesummarizer_service: Optional[FileSummarizerService] = None


def get_filesummarizer_service() -> FileSummarizerService:
    """Get or create the singleton service instance."""
    global _filesummarizer_service
    if _filesummarizer_service is None:
        _filesummarizer_service = FileSummarizerService()
    return _filesummarizer_service
