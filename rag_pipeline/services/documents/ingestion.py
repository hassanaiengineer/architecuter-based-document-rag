from __future__ import annotations

import json
import logging
from pathlib import Path

import anyio

from construction_rag.core.config import Settings
from construction_rag.core.errors import ProcessingError
from construction_rag.core.paths import StoragePaths
from construction_rag.services.embeddings.chunking import Chunker
from construction_rag.services.embeddings.embedder import Embedder
from construction_rag.services.embeddings.faiss_store import FaissVectorStore
from construction_rag.services.ocr.service import OcrService

logger = logging.getLogger(__name__)


class DocumentIngestionService:
    def __init__(self, *, settings: Settings, paths: StoragePaths):
        self._settings = settings
        self._paths = paths
        self._ocr = OcrService(settings)
        self._chunker = Chunker()
        openai_key = settings.openai_api_key.get_secret_value() if settings.openai_api_key else ""
        self._embedder = Embedder(api_key=openai_key, model=settings.embedding_model)

    def _write_outputs(
        self,
        *,
        document_id: str,
        pages: list[dict],
    ) -> tuple[Path, Path]:
        structured_path = self._paths.structured_dir / f"{document_id}.json"
        extracted_path = self._paths.extracted_text_dir / f"{document_id}.txt"
        with structured_path.open("w", encoding="utf-8") as f:
            json.dump({"pages": pages}, f, ensure_ascii=False, indent=2)
        with extracted_path.open("w", encoding="utf-8") as f:
            for p in pages:
                f.write(f"\n\n=== PAGE {p['page_number']} ({p['method']}) ===\n\n")
                f.write(p["text"])
        return structured_path, extracted_path

    def _build_chunks(self, *, pages: list[dict]):
        chunks = []
        for p in pages:
            chunks.extend(self._chunker.chunk_page(page_number=int(p["page_number"]), text=p["text"]))
        if not chunks:
            raise ProcessingError("No text chunks could be created from the document.")
        return chunks

    def _persist_index(self, *, document_id: str, embeddings, chunks) -> tuple[Path, int]:
        index_dir = self._paths.indexes_dir / document_id
        store = FaissVectorStore(index_dir)
        store.build(embeddings=embeddings, chunks=chunks)
        return index_dir, len(chunks)

    async def ingest(self, *, document_id: str, pdf_path: Path) -> dict:
        if not pdf_path.exists():
            raise ProcessingError(f"Uploaded PDF not found: {pdf_path}")

        def run_ocr_sync() -> list[dict]:
            page_texts = self._ocr.extract_pages(pdf_path)
            return [
                {"page_number": p.page_number, "text": p.text, "method": p.method}
                for p in page_texts
            ]

        pages = await anyio.to_thread.run_sync(run_ocr_sync)
        structured_path, extracted_path = self._write_outputs(document_id=document_id, pages=pages)
        chunks = self._build_chunks(pages=pages)
        embeddings = await self._embedder.embed_texts([c.text for c in chunks])
        index_dir, chunk_count = await anyio.to_thread.run_sync(
            lambda: self._persist_index(document_id=document_id, embeddings=embeddings, chunks=chunks)
        )

        return {
            "pages": len(pages),
            "chunks": chunk_count,
            "structured_path": str(structured_path),
            "extracted_text_path": str(extracted_path),
            "index_dir": str(index_dir),
        }
