"""CSV file summarizer."""

from pathlib import Path
from typing import Any

import pandas as pd


class CSVSummarizer:
    """Handles CSV file summarization."""

    def __init__(self, config: dict[str, Any]) -> None:
        self.config = config

    def summarize(self, path: Path) -> str:
        """Generate summary of CSV file using pandas."""
        nrows = self.config["max_rows_to_read"]
        df = pd.read_csv(path, nrows=nrows)
        df_full = pd.read_csv(path)
        total_rows = len(df_full)

        lines = []
        lines.append(f"CSV file: {path.name}")
        lines.append(f"Total rows: {total_rows}")
        lines.append(f"Columns: {', '.join(df.columns)}")
        lines.append("")

        if self.config["include_dtypes"]:
            lines.append("Column types:")
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
