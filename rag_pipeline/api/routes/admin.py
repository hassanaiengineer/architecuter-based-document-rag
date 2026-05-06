from __future__ import annotations

from __future__ import annotations

import secrets
import shutil
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from construction_rag.api.deps import get_db_session, get_paths, get_settings
from construction_rag.core.config import Settings
from construction_rag.core.paths import StoragePaths
from construction_rag.db.models import ChatMessage, Document, DocumentStatus

from construction_rag.api.schemas.admin import HealthOut

router = APIRouter()


@router.get("/health", response_model=HealthOut)
async def health() -> HealthOut:
    return HealthOut(status="ok")


def _require_admin(request: Request, settings: Settings) -> None:
    secret = settings.admin_api_key.get_secret_value() if settings.admin_api_key else ""
    if not secret:
        raise HTTPException(status_code=403, detail="Admin API is disabled (set ADMIN_API_KEY).")
    provided = request.headers.get("X-Admin-Key", "")
    if not secrets.compare_digest(provided, secret):
        raise HTTPException(status_code=403, detail="Invalid admin key.")


@router.get("/stats/documents")
async def document_stats(session: AsyncSession = Depends(get_db_session)):
    total = (await session.execute(select(func.count(Document.id)))).scalar_one()
    by_status = (
        await session.execute(select(Document.status, func.count(Document.id)).group_by(Document.status))
    ).all()
    completed = await session.execute(
        select(func.sum(Document.pages), func.sum(Document.chunks)).where(Document.status == DocumentStatus.completed)
    )
    sum_pages, sum_chunks = completed.one()
    return {
        "total_documents": int(total or 0),
        "by_status": {status.value: int(count) for status, count in by_status},
        "total_pages_completed": int(sum_pages or 0),
        "total_chunks_completed": int(sum_chunks or 0),
    }


@router.get("/stats/storage")
async def storage_stats(paths: StoragePaths = Depends(get_paths)):
    def dir_size_mb(p: Path) -> float:
        total = 0
        if p.exists():
            for fp in p.rglob("*"):
                if fp.is_file():
                    try:
                        total += fp.stat().st_size
                    except FileNotFoundError:
                        pass
        return round(total / (1024 * 1024), 3)

    return {
        "uploads_mb": dir_size_mb(paths.uploads_dir),
        "structured_mb": dir_size_mb(paths.structured_dir),
        "extracted_text_mb": dir_size_mb(paths.extracted_text_dir),
        "indexes_mb": dir_size_mb(paths.indexes_dir),
    }


@router.post("/reset")
async def reset_application(
    request: Request,
    settings: Settings = Depends(get_settings),
    session: AsyncSession = Depends(get_db_session),
    paths: StoragePaths = Depends(get_paths),
):
    _require_admin(request, settings)

    # Clear DB
    await session.execute(delete(ChatMessage))
    await session.execute(delete(Document))
    await session.commit()

    # Clear stored files (keep base dir + db file)
    for directory in [
        paths.uploads_dir,
        paths.pages_dir,
        paths.extracted_text_dir,
        paths.structured_dir,
        paths.indexes_dir,
    ]:
        shutil.rmtree(directory, ignore_errors=True)
        directory.mkdir(parents=True, exist_ok=True)

    return {"message": "Application reset completed."}
