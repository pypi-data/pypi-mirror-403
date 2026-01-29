"""PDF file reader."""

from pathlib import Path
from typing import Any

import pypdf


class PDFReader:
    """Handles PDF file reading with pagination."""

    def __init__(self, config: dict[str, Any], max_lines: int):
        self.config = config
        self.max_lines = max_lines

    def read(self, path: Path, start: int, end: int) -> tuple[str, int, bool]:
        """Read PDF pages from start to end (exclusive).

        Args:
            path: Path to the PDF file
            start: Starting page number (0-indexed)
            end: Ending page number (exclusive)

        Returns:
            Tuple of (content, total_pages, truncated)
        """
        reader = pypdf.PdfReader(path)
        total_pages = len(reader.pages)

        actual_end = min(end, total_pages)

        lines = []
        lines.append(f"PDF Document: {path.name}")
        lines.append(
            f"Reading pages {start} to {actual_end-1} (of {total_pages} total pages)"
        )
        lines.append("")

        for i in range(start, actual_end):
            page = reader.pages[i]
            text = page.extract_text()
            lines.append(f"--- Page {i + 1} ---")
            lines.append(text.strip())
            lines.append("")

        full_output = "\n".join(lines)
        output_lines_list = full_output.split("\n")

        truncated = len(output_lines_list) > self.max_lines
        if truncated:
            truncation_msg = f"\n... [Truncated: showing {self.max_lines} of {len(full_output.split(chr(10)))} lines]"
            output_lines_list = output_lines_list[: self.max_lines] + [truncation_msg]

        return "\n".join(output_lines_list), total_pages, truncated

        return "\n".join(output_lines), total_pages, truncated
