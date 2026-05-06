from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from construction_rag.db.models import Document, DocumentStatus


class DocumentRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def create(
        self,
        *,
        document_id: str,
        filename: str,
        original_filename: str,
        upload_path: str,
    ) -> Document:
        doc = Document(
            id=document_id,
            filename=filename,
            original_filename=original_filename,
            status=DocumentStatus.pending,
            progress=0,
            message="Uploaded; waiting for processing.",
            upload_path=upload_path,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        self._session.add(doc)
        await self._session.commit()
        return doc

    async def get(self, document_id: str) -> Document | None:
        result = await self._session.execute(select(Document).where(Document.id == document_id))
        return result.scalar_one_or_none()

    async def list(self, *, limit: int = 50, offset: int = 0) -> list[Document]:
        result = await self._session.execute(
            select(Document).order_by(Document.created_at.desc()).limit(limit).offset(offset)
        )
        return list(result.scalars().all())

    async def update(self, document_id: str, **updates: Any) -> Document | None:
        doc = await self.get(document_id)
        if not doc:
            return None
        for key, value in updates.items():
            setattr(doc, key, value)
        doc.updated_at = datetime.utcnow()
        await self._session.commit()
        return doc

    async def set_status(
        self,
        document_id: str,
        *,
        status: DocumentStatus,
        progress: int | None = None,
        message: str | None = None,
        **extra: Any,
    ) -> Document | None:
        updates: dict[str, Any] = {"status": status}
        if progress is not None:
            updates["progress"] = progress
        if message is not None:
            updates["message"] = message
        updates.update(extra)
        return await self.update(document_id, **updates)

