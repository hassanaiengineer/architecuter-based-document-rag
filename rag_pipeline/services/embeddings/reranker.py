from __future__ import annotations

import re
from dataclasses import dataclass

from rank_bm25 import BM25Okapi


@dataclass(frozen=True, slots=True)
class RerankedItem:
    index: int
    score: float


_token_re = re.compile(r"[A-Za-z0-9_]+")


def _tokenize(text: str) -> list[str]:
    return [m.group(0).lower() for m in _token_re.finditer(text)]


class Bm25Reranker:
    def rerank(self, *, query: str, passages: list[str]) -> list[RerankedItem]:
        tokenized = [_tokenize(p) for p in passages]
        bm25 = BM25Okapi(tokenized)
        scores = bm25.get_scores(_tokenize(query))
        return sorted(
            (RerankedItem(index=i, score=float(s)) for i, s in enumerate(scores)),
            key=lambda x: x.score,
            reverse=True,
        )

