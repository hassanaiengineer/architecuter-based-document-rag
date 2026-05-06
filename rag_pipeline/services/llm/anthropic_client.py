from __future__ import annotations

import logging

from anthropic import AsyncAnthropic

from construction_rag.core.errors import ConfigError
from construction_rag.services.llm.base import ChatMessage, LlmClient, LlmResult

logger = logging.getLogger(__name__)


class AnthropicClient(LlmClient):
    def __init__(self, *, api_key: str, model: str):
        if not api_key:
            raise ConfigError("ANTHROPIC_API_KEY is required for Anthropic provider.")
        if not model:
            raise ConfigError("LLM_MODEL must be set for Anthropic provider.")
        self._client = AsyncAnthropic(api_key=api_key)
        self._model = model

    async def generate(self, *, messages: list[ChatMessage], max_tokens: int) -> LlmResult:
        system = None
        non_system: list[dict] = []
        for m in messages:
            if m.role == "system":
                system = m.content if system is None else (system + "\n" + m.content)
            else:
                non_system.append({"role": m.role, "content": m.content})

        resp = await self._client.messages.create(
            model=self._model,
            max_tokens=max_tokens,
            system=system,
            messages=non_system,
        )

        text = "".join(block.text for block in resp.content if getattr(block, "text", None))
        usage = getattr(resp, "usage", None)
        return LlmResult(
            text=text,
            input_tokens=getattr(usage, "input_tokens", None),
            output_tokens=getattr(usage, "output_tokens", None),
        )

