"""Generic agent shim."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Iterable, Literal, Optional, Sequence, cast

from namespaces.base.config import load_yaml_config

AnthropicRole = Literal["user", "assistant"]


@dataclass(frozen=True)
class AgentMessage:
    role: str
    content: str


@dataclass(frozen=True)
class AgentResponse:
    text: str
    model: str


class GenericAgent:
    """Generic agent interface for tool output processing.

    The agent accepts a system prompt and chat history and returns a response
    string. Uses AsyncAnthropic for non-blocking API calls.
    """

    def __init__(self) -> None:
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise RuntimeError(
                "ANTHROPIC_API_KEY environment variable is required but not set. "
                "Please set it in your .env file or environment."
            )
        self._model = os.getenv("ANTHROPIC_MODEL", "claude-haiku-4-5")
        config = load_yaml_config("agent")
        self._max_tokens = int(config["max_tokens"])
        self._client = self._build_async_client(api_key)

    async def run(
        self, *, system_prompt: str, messages: Iterable[AgentMessage]
    ) -> Optional[AgentResponse]:
        try:
            return await self._call_api(system_prompt, list(messages))
        except Exception:
            return None

    def _build_async_client(self, api_key: str) -> object:
        import anthropic

        return anthropic.AsyncAnthropic(api_key=api_key)

    async def _call_api(
        self, system_prompt: str, messages: Sequence[AgentMessage]
    ) -> AgentResponse:
        from anthropic.types import MessageParam

        def _coerce_role(role: str) -> AnthropicRole:
            return "assistant" if role == "assistant" else "user"

        anthropic_messages: list[MessageParam] = [
            cast(
                MessageParam,
                {"role": _coerce_role(message.role), "content": message.content},
            )
            for message in messages
        ]
        response = await self._client.messages.create(  # type: ignore
            model=self._model,
            system=system_prompt,
            messages=anthropic_messages,
            max_tokens=self._max_tokens,
        )
        content = ""
        for block in response.content or []:
            if getattr(block, "type", None) == "text":
                content += getattr(block, "text", "")
        if not content:
            content = str(response)
        return AgentResponse(text=content.strip(), model=self._model)
