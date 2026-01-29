"""Excel file reader."""

from pathlib import Path
from typing import Any

import pandas as pd


class XLSXReader:
    """Handles Excel file reading with pagination."""

    def __init__(self, config: dict[str, Any], max_lines: int):
        self.config = config
        self.max_lines = max_lines

    def read(self, path: Path, start: int, end: int) -> tuple[str, int, bool]:
        """Read Excel file rows from start to end (exclusive).

        For multi-sheet Excel files, rows are numbered sequentially across all sheets.
        For example, if Sheet1 has 100 rows and Sheet2 has 50 rows:
        - Rows 0-99 are from Sheet1
        - Rows 100-149 are from Sheet2

        Returns:
            Tuple of (content, total_rows_across_all_sheets, truncated)
        """
        excel_file = pd.ExcelFile(path)
        sheet_names = excel_file.sheet_names

        sheets_data = []
        cumulative_rows = []
        current_total = 0

        for sheet_name in sheet_names:
            df = pd.read_excel(path, sheet_name=sheet_name)
            sheets_data.append((sheet_name, df))
            cumulative_rows.append(current_total)
            current_total += len(df)

        total_rows = current_total

        lines = []
        lines.append(f"Excel file: {path.name}")
        lines.append(
            f"Reading rows {start} to {min(end, total_rows)} (of {total_rows} total rows across all sheets)"
        )
        lines.append("")

        for idx, (sheet_name, df) in enumerate(sheets_data):
            sheet_start = cumulative_rows[idx]
            sheet_end = sheet_start + len(df)

            if end <= sheet_start or start >= sheet_end:
                continue

            local_start = max(0, start - sheet_start)
            local_end = min(len(df), end - sheet_start)

            df_slice = df.iloc[local_start:local_end]

            if not df_slice.empty:
                lines.append(
                    f"Sheet: {sheet_name} (rows {sheet_start} to {sheet_end-1})"
                )
                lines.append(f"Columns: {', '.join(df.columns)}")
                lines.append("")
                lines.append(df_slice.to_string(index=True))
                lines.append("")

        full_output = "\n".join(lines)
        output_lines_list = full_output.split("\n")

        truncated = len(output_lines_list) > self.max_lines
        if truncated:
            truncation_msg = f"\n... [Truncated: showing {self.max_lines} of {len(full_output.split(chr(10)))} lines]"
            output_lines_list = output_lines_list[: self.max_lines] + [truncation_msg]

        return "\n".join(output_lines_list), total_rows, truncated
