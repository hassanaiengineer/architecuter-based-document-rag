from __future__ import annotations

import logging
import secrets
from datetime import datetime
from pathlib import Path

import anyio
from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from construction_rag.api.deps import get_db_session, get_paths, get_settings
from construction_rag.api.schemas.documents import (
    DocumentListOut,
    DocumentOut,
    DocumentStatusOut,
    UploadResponse,
)
from construction_rag.core.config import Settings
from construction_rag.core.errors import NotFoundError
from construction_rag.core.paths import StoragePaths
from construction_rag.db.models import DocumentStatus
from construction_rag.db.repositories.documents import DocumentRepository
from construction_rag.services.documents.ingestion import DocumentIngestionService

logger = logging.getLogger(__name__)
router = APIRouter()


def _new_document_id() -> str:
    ts = int(datetime.utcnow().timestamp())
    return f"{ts}_{secrets.token_hex(4)}"


@router.post("", response_model=UploadResponse)
async def upload_document(
    request: Request,
    file: UploadFile = File(...),
    settings: Settings = Depends(get_settings),
    session: AsyncSession = Depends(get_db_session),
    paths: StoragePaths = Depends(get_paths),
):
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF uploads are supported.")

    document_id = _new_document_id()
    upload_path = paths.uploads_dir / f"{document_id}.pdf"
    async with await anyio.open_file(upload_path, "wb") as out:
        while True:
            chunk = await file.read(1024 * 1024)
            if not chunk:
                break
            await out.write(chunk)

    repo = DocumentRepository(session)
    await repo.create(
        document_id=document_id,
        filename=file.filename,
        original_filename=file.filename,
        upload_path=str(upload_path),
    )

    session_factory = request.app.state.session_factory
    semaphore = request.app.state.ingestion_semaphore
    ingestion = DocumentIngestionService(settings=settings, paths=paths)

    async def run_ingestion() -> None:
        async with semaphore:
            async with session_factory() as bg_session:
                bg_repo = DocumentRepository(bg_session)
                await bg_repo.set_status(
                    document_id,
                    status=DocumentStatus.processing,
                    progress=5,
                    message="Extracting text from PDF...",
                )
                try:
                    result = await ingestion.ingest(document_id=document_id, pdf_path=Path(upload_path))
                    await bg_repo.set_status(
                        document_id,
                        status=DocumentStatus.completed,
                        progress=100,
                        message="Document processed successfully.",
                        pages=result["pages"],
                        chunks=result["chunks"],
                        structured_path=result["structured_path"],
                        extracted_text_path=result["extracted_text_path"],
                        index_dir=result["index_dir"],
                    )
                except Exception as exc:
                    logger.exception("Document ingestion failed: %s", exc)
                    await bg_repo.set_status(
                        document_id,
                        status=DocumentStatus.failed,
                        progress=100,
                        message=str(exc),
                    )

    return UploadResponse(id=document_id, status="pending")


@router.get("", response_model=DocumentListOut)
async def list_documents(
    session: AsyncSession = Depends(get_db_session),
    limit: int = 50,
    offset: int = 0,
):
    repo = DocumentRepository(session)
    docs = await repo.list(limit=limit, offset=offset)
    return DocumentListOut(
        documents=[
            DocumentOut(
                id=d.id,
                filename=d.filename,
                status=d.status.value,
                progress=d.progress,
                message=d.message,
                pages=d.pages,
                chunks=d.chunks,
                created_at=d.created_at,
                updated_at=d.updated_at,
            )
            for d in docs
        ]
    )


@router.get("/{document_id}", response_model=DocumentOut)
async def get_document(document_id: str, session: AsyncSession = Depends(get_db_session)):
    repo = DocumentRepository(session)
    doc = await repo.get(document_id)
    if not doc:
        raise NotFoundError("Document not found.")
    return DocumentOut(
        id=doc.id,
        filename=doc.filename,
        status=doc.status.value,
        progress=doc.progress,
        message=doc.message,
        pages=doc.pages,
        chunks=doc.chunks,
        created_at=doc.created_at,
        updated_at=doc.updated_at,
    )


@router.get("/{document_id}/status", response_model=DocumentStatusOut)
async def document_status(document_id: str, session: AsyncSession = Depends(get_db_session)):
    repo = DocumentRepository(session)
    doc = await repo.get(document_id)
    if not doc:
        raise NotFoundError("Document not found.")
    return DocumentStatusOut(id=doc.id, status=doc.status.value, progress=doc.progress, message=doc.message)
