"""Shared output truncation and summarization helpers."""

from __future__ import annotations

from typing import Optional

from namespaces.base.config import load_yaml_config
from namespaces.base.summarizer import ToolOutputSummarizer


class OutputProcessor:
    """Truncates tool output and optionally summarizes it via an LLM."""

    def __init__(self, namespace: str) -> None:
        config = load_yaml_config("output_formatter")
        self.head_chars = int(config["head_chars"])
        self.tail_chars = int(config["tail_chars"])
        self.max_output_chars = self.head_chars + self.tail_chars
        self.summary_head_chars = int(config["summary_head_chars"])
        self.summary_tail_chars = int(config["summary_tail_chars"])
        self.summarizer = ToolOutputSummarizer(namespace)

    def char_count(self, text: str) -> int:
        """Count characters in text."""
        if not text:
            return 0
        return len(text)

    def total_chars(self, texts: list[str]) -> int:
        """Count total characters across multiple texts."""
        return sum(self.char_count(text) for text in texts)

    def _truncate_by_chars(
        self, text: str, *, head_chars: int, tail_chars: int
    ) -> tuple[str, bool]:
        """Truncate text to head/tail by character count."""
        if not text:
            return "", False

        total_chars = len(text)
        if total_chars <= head_chars + tail_chars:
            return text, False

        head = text[:head_chars]
        tail = text[-tail_chars:]
        middle_count = total_chars - head_chars - tail_chars
        truncated = f"{head}\n... {middle_count} chars truncated ...\n{tail}"
        return truncated, True

    def truncate_text(self, text: str) -> tuple[str, bool]:
        """Truncate text to head/tail if too long."""
        if not text:
            return "", False

        if len(text) <= self.max_output_chars:
            return text, False

        return self._truncate_by_chars(
            text, head_chars=self.head_chars, tail_chars=self.tail_chars
        )

    async def process(
        self, *, query: str, output: str, prompt: str, force_refresh: bool
    ) -> tuple[str, bool, Optional[str]]:
        """Process output: truncate if needed, summarize if truncated.

        Returns (output, truncated, summary).
        """
        total_chars = self.char_count(output)
        if total_chars <= self.max_output_chars:
            return output, False, None

        truncated_text, _ = self.truncate_text(output)
        summary_source, _ = self._truncate_by_chars(
            output,
            head_chars=self.summary_head_chars,
            tail_chars=self.summary_tail_chars,
        )
        combined = f"[Output truncated]\n{summary_source}"
        summary_text = await self._summarize(
            command=query,
            summary_hint=None,
            output=combined,
            exit_code=0,
            system_prompt=prompt,
            force_refresh=force_refresh,
        )
        if not summary_text:
            summary_text = (
                f"Output returned {total_chars} chars. Truncated to head/tail."
            )
        return truncated_text, True, summary_text

    async def _summarize(
        self,
        *,
        command: str,
        summary_hint: Optional[str],
        output: str,
        exit_code: int,
        system_prompt: str,
        force_refresh: bool,
    ) -> Optional[str]:
        """Summarize output using the LLM."""
        summary = await self.summarizer.summarize(
            command=command,
            summary_hint=summary_hint,
            output=output,
            exit_code=exit_code,
            system_prompt=system_prompt,
            force_refresh=force_refresh,
        )
        if summary:
            return summary.text
        return None
