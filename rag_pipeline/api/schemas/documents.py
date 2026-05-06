from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel, Field


class DocumentOut(BaseModel):
    id: str
    filename: str
    status: str
    progress: int = 0
    message: str | None = None
    pages: int | None = None
    chunks: int | None = None
    created_at: datetime
    updated_at: datetime


class DocumentListOut(BaseModel):
    documents: list[DocumentOut]


class DocumentStatusOut(BaseModel):
    id: str
    status: str
    progress: int
    message: str | None = None


class UploadResponse(BaseModel):
    id: str = Field(..., description="Document ID")
    status: str

