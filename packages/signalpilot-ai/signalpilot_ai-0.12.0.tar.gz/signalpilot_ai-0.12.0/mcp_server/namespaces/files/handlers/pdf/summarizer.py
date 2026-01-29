"""PDF file summarizer."""

from pathlib import Path
from typing import Any

import pypdf


class PDFSummarizer:
    """Handles PDF file summarization."""

    def __init__(self, config: dict[str, Any]) -> None:
        self.config = config

    def summarize(self, path: Path) -> str:
        """Generate summary of PDF file.

        Note: For reading specific pages, use the reader service.
        Pages are numbered starting from 0.
        """
        reader = pypdf.PdfReader(path)

        lines = []
        lines.append(f"PDF Document: {path.name}")
        lines.append(f"Total pages: {len(reader.pages)}")
        lines.append("")

        metadata = reader.metadata
        if metadata:
            lines.append("Metadata:")
            if metadata.title:
                lines.append(f"  Title: {metadata.title}")
            if metadata.author:
                lines.append(f"  Author(s): {metadata.author}")
            if metadata.subject:
                lines.append(f"  Subject: {metadata.subject}")
            if metadata.creator:
                lines.append(f"  Creator: {metadata.creator}")
            lines.append("")

        outline = reader.outline
        if outline:
            lines.append("Table of Contents / Index:")
            self._format_outline(outline, lines, indent=1)
            lines.append("")

        max_pages = self.config["max_pages_to_read"]
        pages_to_read = min(max_pages, len(reader.pages))
        lines.append(f"Content (first {pages_to_read} pages):")
        lines.append("")

        for i in range(pages_to_read):
            page = reader.pages[i]
            text = page.extract_text()
            lines.append(f"--- Page {i + 1} ---")
            lines.append(text.strip())
            lines.append("")

        return "\n".join(lines)

    def _format_outline(self, outline: list, lines: list[str], indent: int = 0) -> None:
        """Recursively format PDF outline/table of contents."""
        for item in outline:
            if isinstance(item, list):
                self._format_outline(item, lines, indent + 1)
            else:
                prefix = "  " * indent
                title = item.title if hasattr(item, "title") else str(item)
                lines.append(f"{prefix}- {title}")
