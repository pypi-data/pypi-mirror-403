"""Excel file summarizer."""

from pathlib import Path
from typing import Any

import pandas as pd


class XLSXSummarizer:
    """Handles Excel file summarization."""

    def __init__(self, config: dict[str, Any]) -> None:
        self.config = config

    def summarize(self, path: Path) -> str:
        """Generate summary of Excel file using pandas.

        Note: For reading specific rows, use the reader service.
        Each sheet is independent - AI should track sheet boundaries using total row counts.
        """
        excel_file = pd.ExcelFile(path)
        sheet_names = excel_file.sheet_names

        lines = []
        lines.append(f"Excel file: {path.name}")
        lines.append(f"Total sheets: {len(sheet_names)}")
        lines.append("")

        for sheet_name in sheet_names:
            df = pd.read_excel(path, sheet_name=sheet_name)
            lines.append(f"Sheet: {sheet_name}")
            lines.append(f"Total rows in this sheet: {df.shape[0]}")
            lines.append(f"Columns: {', '.join(df.columns)}")
            lines.append("")
            lines.append("Top 5 rows:")
            lines.append(str(df.head(5)))
            lines.append("")

        return "\n".join(lines)
