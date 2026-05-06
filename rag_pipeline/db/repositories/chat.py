from __future__ import annotations

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from construction_rag.db.models import ChatMessage


class ChatRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def add(
        self,
        *,
        document_id: str,
        role: str,
        content: str,
        metadata_json: dict | None = None,
    ) -> ChatMessage:
        msg = ChatMessage(
            document_id=document_id,
            role=role,
            content=content,
            metadata_json=metadata_json,
        )
        self._session.add(msg)
        await self._session.commit()
        return msg

    async def list(self, document_id: str, *, limit: int = 200) -> list[ChatMessage]:
        result = await self._session.execute(
            select(ChatMessage)
            .where(ChatMessage.document_id == document_id)
            .order_by(ChatMessage.id.asc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def clear(self, document_id: str) -> None:
        await self._session.execute(delete(ChatMessage).where(ChatMessage.document_id == document_id))
        await self._session.commit()

