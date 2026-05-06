from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from construction_rag.core.config import Settings
from construction_rag.services.embeddings.faiss_store import RetrievedChunk
from construction_rag.services.embeddings.reranker import Bm25Reranker
from construction_rag.services.llm.base import ChatMessage, LlmClient
from construction_rag.services.rag.prompts import SYSTEM_PROMPT, build_user_prompt

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class RagAnswer:
    answer: str
    citations: list[dict[str, Any]]
    input_tokens: int | None = None
    output_tokens: int | None = None


class RagPipeline:
    def __init__(self, *, settings: Settings, llm: LlmClient):
        self._settings = settings
        self._llm = llm
        self._reranker = Bm25Reranker() if settings.rerank_mode == "bm25" else None

    def rerank_if_enabled(self, *, query: str, items: list[RetrievedChunk], top_k: int) -> list[RetrievedChunk]:
        if not items:
            return []
        if not self._reranker:
            return items[:top_k]
        passages = [i.text for i in items[: self._settings.rerank_top_n]]
        reranked = self._reranker.rerank(query=query, passages=passages)
        ordered = [items[r.index] for r in reranked]
        return ordered[:top_k]

    async def answer(
        self,
        *,
        question: str,
        retrieved: list[RetrievedChunk],
        max_tokens: int,
    ) -> RagAnswer:
        context_blocks = []
        citations: list[dict[str, Any]] = []

        for r in retrieved:
            context_blocks.append(f"[p.{r.page_number}] {r.text}")
            citations.append(
                {
                    "chunk_id": r.chunk_id,
                    "page_number": r.page_number,
                    "score": r.score,
                    "excerpt": r.text[:300],
                }
            )

        messages = [
            ChatMessage(role="system", content=SYSTEM_PROMPT),
            ChatMessage(role="user", content=build_user_prompt(question=question, context_blocks=context_blocks)),
        ]
        result = await self._llm.generate(messages=messages, max_tokens=max_tokens)
        return RagAnswer(
            answer=result.text.strip(),
            citations=citations,
            input_tokens=result.input_tokens,
            output_tokens=result.output_tokens,
        )
