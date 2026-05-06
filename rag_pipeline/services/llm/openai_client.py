from __future__ import annotations

from openai import AsyncOpenAI

from construction_rag.core.errors import ConfigError
from construction_rag.services.llm.base import ChatMessage, LlmClient, LlmResult


class OpenAiClient(LlmClient):
    def __init__(self, *, api_key: str, model: str):
        if not api_key:
            raise ConfigError("OPENAI_API_KEY is required for OpenAI provider.")
        if not model:
            raise ConfigError("LLM_MODEL must be set for OpenAI provider.")
        self._client = AsyncOpenAI(api_key=api_key)
        self._model = model

    async def generate(self, *, messages: list[ChatMessage], max_tokens: int) -> LlmResult:
        resp = await self._client.chat.completions.create(
            model=self._model,
            messages=[{"role": m.role, "content": m.content} for m in messages],
            max_tokens=max_tokens,
            temperature=0.2,
        )
        choice = resp.choices[0]
        text = (choice.message.content or "").strip()
        usage = getattr(resp, "usage", None)
        return LlmResult(
            text=text,
            input_tokens=getattr(usage, "prompt_tokens", None),
            output_tokens=getattr(usage, "completion_tokens", None),
        )

