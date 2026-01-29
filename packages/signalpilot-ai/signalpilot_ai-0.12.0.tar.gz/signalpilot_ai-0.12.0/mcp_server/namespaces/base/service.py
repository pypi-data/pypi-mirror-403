"""Base service class for all namespace services."""

from __future__ import annotations

from pathlib import Path

from namespaces.base.output_processor import OutputProcessor


class BaseService:
    """Base class providing shared functionality for namespace services."""

    prompt_file: str = "prompt.md"

    def __init__(self, namespace: str) -> None:
        self._namespace = namespace
        self._output_processor = OutputProcessor(namespace)
        self._system_prompt = self._load_prompt()

    def _get_prompt_path(self) -> Path:
        """Return path to prompt.md in the service's directory."""
        raise NotImplementedError

    def _load_prompt(self) -> str:
        """Load the system prompt from prompt.md."""
        path = self._get_prompt_path()
        if path.exists():
            return path.read_text().strip()
        return "Summarize output."
