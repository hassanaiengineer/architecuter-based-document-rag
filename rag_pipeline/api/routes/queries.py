from __future__ import annotations

from datetime import datetime
from pathlib import Path

import anyio
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from construction_rag.api.deps import get_db_session, get_settings
from construction_rag.api.schemas.queries import ChatHistoryOut, ChatMessageOut, QueryRequest, QueryResponse
from construction_rag.core.config import Settings
from construction_rag.core.errors import NotFoundError, ProcessingError
from construction_rag.db.models import DocumentStatus
from construction_rag.db.repositories.chat import ChatRepository
from construction_rag.db.repositories.documents import DocumentRepository
from construction_rag.services.embeddings.embedder import Embedder
from construction_rag.services.embeddings.faiss_store import FaissVectorStore
from construction_rag.services.llm.factory import build_llm_client
from construction_rag.services.rag.pipeline import RagPipeline

router = APIRouter()


@router.post("/{document_id}/query", response_model=QueryResponse)
async def query_document(
    document_id: str,
    req: QueryRequest,
    settings: Settings = Depends(get_settings),
    session: AsyncSession = Depends(get_db_session),
):
    doc_repo = DocumentRepository(session)
    doc = await doc_repo.get(document_id)
    if not doc:
        raise NotFoundError("Document not found.")
    if doc.status != DocumentStatus.completed:
        raise ProcessingError(f"Document is not ready (status={doc.status.value}).")
    if not doc.index_dir:
        raise ProcessingError("Document index missing; reprocess the document.")

    llm = build_llm_client(settings)
    pipeline = RagPipeline(settings=settings, llm=llm)

    openai_key = settings.openai_api_key.get_secret_value() if settings.openai_api_key else ""
    embedder = Embedder(api_key=openai_key, model=settings.embedding_model)
    query_embedding = await embedder.embed_query(req.question)

    def retrieve_sync():
        store = FaissVectorStore(Path(doc.index_dir))
        search_k = req.top_k if settings.rerank_mode == "off" else max(req.top_k, settings.rerank_top_n)
        items = store.search(query_embedding=query_embedding, top_k=search_k)
        if req.page_numbers:
            allowed = set(req.page_numbers)
            items = [r for r in items if r.page_number in allowed]
        return pipeline.rerank_if_enabled(query=req.question, items=items, top_k=req.top_k)

    retrieved = await anyio.to_thread.run_sync(retrieve_sync)

    answer = await pipeline.answer(question=req.question, retrieved=retrieved, max_tokens=req.max_tokens)

    created_at = datetime.utcnow()
    if req.save_to_history:
        chat_repo = ChatRepository(session)
        await chat_repo.add(document_id=document_id, role="user", content=req.question, metadata_json=None)
        await chat_repo.add(
            document_id=document_id,
            role="assistant",
            content=answer.answer,
            metadata_json={"citations": answer.citations},
        )

    return QueryResponse(
        document_id=document_id,
        question=req.question,
        answer=answer.answer,
        citations=answer.citations,  # pydantic will coerce
        input_tokens=answer.input_tokens,
        output_tokens=answer.output_tokens,
        created_at=created_at,
    )


@router.get("/{document_id}/chat/history", response_model=ChatHistoryOut)
async def chat_history(document_id: str, session: AsyncSession = Depends(get_db_session)):
    doc_repo = DocumentRepository(session)
    if not await doc_repo.get(document_id):
        raise NotFoundError("Document not found.")

    repo = ChatRepository(session)
    history = await repo.list(document_id)
    return ChatHistoryOut(
        document_id=document_id,
        history=[
            ChatMessageOut(role=m.role, content=m.content, created_at=m.created_at, metadata=m.metadata_json)
            for m in history
        ],
    )


@router.delete("/{document_id}/chat/history")
async def clear_chat(document_id: str, session: AsyncSession = Depends(get_db_session)):
    doc_repo = DocumentRepository(session)
    if not await doc_repo.get(document_id):
        raise NotFoundError("Document not found.")
    repo = ChatRepository(session)
    await repo.clear(document_id)
    return {"message": "Chat history cleared."}
