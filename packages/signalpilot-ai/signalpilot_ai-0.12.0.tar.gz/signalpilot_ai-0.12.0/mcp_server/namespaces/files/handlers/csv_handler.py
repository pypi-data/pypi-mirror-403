"""CSV file handler."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd


class CSVHandler:
    """Handles CSV file summarization."""

    def __init__(self, config: dict[str, Any]) -> None:
        self.config = config

    def summarize(self, path: Path) -> str:
        """Generate summary of CSV file using pandas."""
        nrows = self.config["max_rows_to_read"]
        df = pd.read_csv(path, nrows=nrows)

        lines = []
        lines.append(f"Shape: {df.shape[0]} rows, {df.shape[1]} columns")
        lines.append("")

        if self.config["include_dtypes"]:
            lines.append("Columns:")
            for col in df.columns:
                lines.append(f"  - {col} ({df[col].dtype})")
            lines.append("")

        if self.config["include_statistics"]:
            lines.append("Statistical Summary:")
            lines.append(str(df.describe(include="all")))
            lines.append("")

        if self.config["include_missing_values"]:
            lines.append(f"Missing values:")
            missing = df.isnull().sum()
            if missing.sum() == 0:
                lines.append("  No missing values")
            else:
                for col, count in missing[missing > 0].items():
                    lines.append(f"  - {col}: {count}")
            lines.append("")

        lines.append("First 5 rows:")
        lines.append(str(df.head(5)))

        return "\n".join(lines)

    def read(self, path: Path, start: int, end: int) -> tuple[str, int]:
        """Read CSV file rows from start to end (exclusive).

        Returns:
            Tuple of (content, total_rows)
        """
        df_full = pd.read_csv(path)
        total_rows = len(df_full)

        df_slice = df_full.iloc[start:end]

        lines = []
        lines.append(
            f"CSV rows {start} to {min(end, total_rows)} (of {total_rows} total rows)"
        )
        lines.append(f"Columns: {', '.join(df_full.columns)}")
        lines.append("")
        lines.append(df_slice.to_string(index=True))

        return "\n".join(lines), total_rows
