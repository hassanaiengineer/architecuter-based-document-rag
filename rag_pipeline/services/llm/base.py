from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


Role = Literal["user", "assistant", "system"]


@dataclass(frozen=True, slots=True)
class ChatMessage:
    role: Role
    content: str


@dataclass(frozen=True, slots=True)
class LlmResult:
    text: str
    input_tokens: int | None = None
    output_tokens: int | None = None


class LlmClient:
    async def generate(self, *, messages: list[ChatMessage], max_tokens: int) -> LlmResult:  # pragma: no cover
        raise NotImplementedError

