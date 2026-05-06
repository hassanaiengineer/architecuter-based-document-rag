from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Chunk:
    chunk_id: str
    page_number: int
    text: str


class Chunker:
    def __init__(self, *, chunk_size: int = 900, chunk_overlap: int = 180):
        if chunk_overlap >= chunk_size:
            raise ValueError("chunk_overlap must be < chunk_size")
        self._chunk_size = chunk_size
        self._chunk_overlap = chunk_overlap

    def chunk_page(self, *, page_number: int, text: str) -> list[Chunk]:
        normalized = (text or "").replace("\r\n", "\n").replace("\r", "\n")
        if not normalized.strip():
            return []

        chunks: list[Chunk] = []
        start = 0
        index = 0
        while start < len(normalized):
            end = min(len(normalized), start + self._chunk_size)
            chunk_text = normalized[start:end].strip()
            if chunk_text:
                chunks.append(
                    Chunk(chunk_id=f"p{page_number:04d}_c{index:04d}", page_number=page_number, text=chunk_text)
                )
                index += 1
            if end >= len(normalized):
                break
            start = max(0, end - self._chunk_overlap)
        return chunks

