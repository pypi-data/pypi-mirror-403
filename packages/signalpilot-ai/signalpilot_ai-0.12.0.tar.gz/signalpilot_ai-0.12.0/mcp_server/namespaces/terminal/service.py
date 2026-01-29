"""Terminal tool service with output summarization."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Optional

from namespaces.base.service import BaseService
from namespaces.terminal.executor import TerminalCommandExecutor
from namespaces.terminal.models import (
    GlobRequest,
    GlobResponse,
    GrepMatch,
    GrepRequest,
    GrepResponse,
    TerminalExecuteRequest,
    TerminalExecuteResponse,
)


class TerminalService(BaseService):
    """Coordinates execution and summarization."""

    def __init__(self, *, executor: Optional[TerminalCommandExecutor] = None) -> None:
        super().__init__("terminal")
        self._executor = executor or TerminalCommandExecutor()

    def _get_prompt_path(self) -> Path:
        """Return path to prompt.md in terminal namespace."""
        return Path(__file__).parent / self.prompt_file

    async def execute(self, request: TerminalExecuteRequest) -> TerminalExecuteResponse:
        """Execute command and return processed results."""
        result = await self._executor.run(request.command, request.timeout_seconds)

        combined_output = "\n".join(
            chunk for chunk in (result.stdout, result.stderr) if chunk
        )
        output, truncated, summary = await self._output_processor.process(
            query=request.command,
            output=combined_output,
            prompt=self._system_prompt,
            force_refresh=request.force_refresh,
        )

        return TerminalExecuteResponse(
            exit_code=result.exit_code,
            output=output,
            truncated=truncated,
            summary=summary,
        )

    async def glob(self, request: GlobRequest) -> GlobResponse:
        """Find files matching a glob pattern."""
        base_path = Path(request.path) if request.path else Path.cwd()

        if not base_path.exists():
            return GlobResponse(files=[], count=0, error=f"Path does not exist: {base_path}")

        if not base_path.is_dir():
            return GlobResponse(files=[], count=0, error=f"Path is not a directory: {base_path}")

        try:
            matches = sorted(base_path.glob(request.pattern))
            files = [str(p) for p in matches if p.is_file()]
            return GlobResponse(files=files, count=len(files), error=None)
        except Exception as e:
            return GlobResponse(files=[], count=0, error=str(e))

    async def grep(self, request: GrepRequest) -> GrepResponse:
        """Search file contents using regex."""
        base_path = Path(request.path) if request.path else Path.cwd()

        if not base_path.exists():
            return GrepResponse(
                matches=[], count=0, truncated=False, error=f"Path does not exist: {base_path}"
            )

        try:
            flags = re.IGNORECASE if request.case_insensitive else 0
            regex = re.compile(request.pattern, flags)
        except re.error as e:
            return GrepResponse(
                matches=[], count=0, truncated=False, error=f"Invalid regex pattern: {e}"
            )

        files_to_search = self._get_files_to_search(base_path, request.glob)
        matches: list[GrepMatch] = []
        truncated = False

        for file_path in files_to_search:
            if len(matches) >= request.max_results:
                truncated = True
                break

            file_matches = self._search_file(
                file_path, regex, request.context_lines, request.max_results - len(matches)
            )
            matches.extend(file_matches)

        return GrepResponse(
            matches=matches,
            count=len(matches),
            truncated=truncated,
            error=None,
        )

    def _get_files_to_search(self, base_path: Path, glob_pattern: Optional[str]) -> list[Path]:
        """Get list of files to search based on path and optional glob pattern."""
        if base_path.is_file():
            return [base_path]

        pattern = glob_pattern or "**/*"
        return [p for p in sorted(base_path.glob(pattern)) if p.is_file()]

    def _search_file(
        self,
        file_path: Path,
        regex: re.Pattern,
        context_lines: int,
        max_matches: int,
    ) -> list[GrepMatch]:
        """Search a single file for regex matches."""
        matches: list[GrepMatch] = []

        try:
            lines = file_path.read_text(errors="ignore").splitlines()
        except Exception:
            return matches

        for i, line in enumerate(lines):
            if len(matches) >= max_matches:
                break

            if regex.search(line):
                start = max(0, i - context_lines)
                end = min(len(lines), i + context_lines + 1)

                matches.append(
                    GrepMatch(
                        file=str(file_path),
                        line_number=i + 1,
                        line=line,
                        context_before=lines[start:i],
                        context_after=lines[i + 1 : end],
                    )
                )

        return matches


_terminal_service: Optional[TerminalService] = None


def get_terminal_service() -> TerminalService:
    """Get or create the singleton service instance."""
    global _terminal_service
    if _terminal_service is None:
        _terminal_service = TerminalService()
    return _terminal_service
