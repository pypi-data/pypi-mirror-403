"""Shared LLM summarizer for tool outputs."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from namespaces.base.cache import DiskCache
from namespaces.base.config import load_yaml_config

from .agent import AgentMessage, GenericAgent


@dataclass(frozen=True)
class ToolSummary:
    text: str
    model: str


class ToolOutputSummarizer:
    """Summarizes tool output via the generic agent with caching."""

    def __init__(self, namespace: str) -> None:
        self.agent = GenericAgent()
        config = load_yaml_config("output_formatter")
        cache_dir = Path(config["cache_dir"])
        size_limit_mb = int(config["cache_size_limit_mb"])
        self._cache = DiskCache(cache_dir, namespace, size_limit_mb)

    async def summarize(
        self,
        *,
        command: str,
        summary_hint: Optional[str],
        output: str,
        exit_code: int,
        system_prompt: Optional[str] = None,
        force_refresh: bool,
    ) -> Optional[ToolSummary]:
        prompt = system_prompt or "Summarize tool output for downstream use."
        summary_text = summary_hint.strip() if summary_hint else ""
        message_lines = [
            f"Command: {command}",
            f"Exit code: {exit_code}",
        ]
        if summary_text:
            message_lines.append(f"Intent: {summary_text}")
        if output.strip():
            message_lines.append(f"Output:\n{output.strip()}")

        user_content = "\n".join(message_lines)

        if not force_refresh:
            cached = self._cache.get(output)
            if cached is not None:
                cached_data = json.loads(cached)
                return ToolSummary(text=cached_data["text"], model=cached_data["model"])

        response = await self.agent.run(
            system_prompt=prompt,
            messages=[AgentMessage(role="user", content=user_content)],
        )
        if not response:
            return None

        cache_value = json.dumps({"text": response.text, "model": response.model})
        self._cache.set(output, cache_value)

        return ToolSummary(text=response.text, model=response.model)
