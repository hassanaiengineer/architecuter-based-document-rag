from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass
from pathlib import Path

import faiss
import numpy as np

from construction_rag.services.embeddings.chunking import Chunk

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class RetrievedChunk:
    chunk_id: str
    page_number: int
    score: float
    text: str


class FaissVectorStore:
    def __init__(self, index_dir: Path):
        self._index_dir = index_dir
        self._index_file = index_dir / "index.faiss"
        self._chunks_file = index_dir / "chunks.jsonl"

    def build(self, *, embeddings: np.ndarray, chunks: list[Chunk]) -> None:
        self._index_dir.mkdir(parents=True, exist_ok=True)
        if embeddings.shape[0] != len(chunks):
            raise ValueError("Embeddings count must match chunk count")
        if embeddings.dtype != np.float32:
            embeddings = embeddings.astype(np.float32)

        dim = int(embeddings.shape[1])
        index = faiss.IndexFlatIP(dim)
        index.add(embeddings)
        faiss.write_index(index, str(self._index_file))

        with self._chunks_file.open("w", encoding="utf-8") as f:
            for c in chunks:
                f.write(json.dumps(asdict(c), ensure_ascii=False) + "\n")

        logger.info("Built FAISS index at %s with %s chunks", self._index_file, len(chunks))

    def _load(self) -> tuple[list[Chunk], faiss.Index]:
        if not self._index_file.exists() or not self._chunks_file.exists():
            raise FileNotFoundError("Index not found. Document must be processed first.")
        index = faiss.read_index(str(self._index_file))
        chunks: list[Chunk] = []
        with self._chunks_file.open("r", encoding="utf-8") as f:
            for line in f:
                obj = json.loads(line)
                chunks.append(Chunk(chunk_id=obj["chunk_id"], page_number=int(obj["page_number"]), text=obj["text"]))
        return chunks, index

    def search(self, *, query_embedding: np.ndarray, top_k: int) -> list[RetrievedChunk]:
        chunks, index = self._load()

        q = np.asarray(query_embedding, dtype=np.float32).reshape(1, -1)
        scores, indices = index.search(q, top_k)

        results: list[RetrievedChunk] = []
        for idx, score in zip(indices[0], scores[0], strict=False):
            if idx < 0 or idx >= len(chunks):
                continue
            c = chunks[int(idx)]
            results.append(
                RetrievedChunk(
                    chunk_id=c.chunk_id,
                    page_number=c.page_number,
                    score=float(score),
                    text=c.text,
                )
            )
        return results

