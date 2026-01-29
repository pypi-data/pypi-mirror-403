"""CSV file reader."""

from pathlib import Path
from typing import Any

import pandas as pd


class CSVReader:
    """Handles CSV file reading with pagination."""

    def __init__(self, config: dict[str, Any], max_lines: int):
        self.config = config
        self.max_lines = max_lines

    def read(self, path: Path, start: int, end: int) -> tuple[str, int, bool]:
        """Read CSV file rows from start to end (exclusive).

        Returns:
            Tuple of (content, total_rows, truncated)
        """
        df_full = pd.read_csv(path)
        total_rows = len(df_full)

        df_slice = df_full.iloc[start:end]

        lines = []
        lines.append(f"CSV file: {path.name}")
        lines.append(
            f"Rows {start} to {min(end, total_rows)} (of {total_rows} total rows)"
        )
        lines.append(f"Columns: {', '.join(df_full.columns)}")
        lines.append("")

        content_str = df_slice.to_string(index=True)
        lines.append(content_str)

        full_output = "\n".join(lines)
        output_lines_list = full_output.split("\n")

        truncated = len(output_lines_list) > self.max_lines
        if truncated:
            truncation_msg = f"\n... [Truncated: showing {self.max_lines} of {len(full_output.split(chr(10)))} lines]"
            output_lines_list = output_lines_list[: self.max_lines] + [truncation_msg]

        return "\n".join(output_lines_list), total_rows, truncated
