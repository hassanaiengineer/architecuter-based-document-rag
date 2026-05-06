from __future__ import annotations

from construction_rag.core.config import Settings
from construction_rag.services.llm.anthropic_client import AnthropicClient
from construction_rag.services.llm.base import LlmClient
from construction_rag.services.llm.openai_client import OpenAiClient


def build_llm_client(settings: Settings) -> LlmClient:
    model = settings.llm_model or ""
    if settings.llm_provider == "anthropic":
        key = settings.anthropic_api_key.get_secret_value() if settings.anthropic_api_key else ""
        return AnthropicClient(api_key=key, model=model)
    key = settings.openai_api_key.get_secret_value() if settings.openai_api_key else ""
    return OpenAiClient(api_key=key, model=model)

