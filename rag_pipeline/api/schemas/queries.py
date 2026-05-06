from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    question: str = Field(..., min_length=3)
    top_k: int = Field(default=6, ge=1, le=30)
    max_tokens: int = Field(default=800, ge=64, le=4096)
    save_to_history: bool = True
    page_numbers: list[int] | None = Field(
        default=None, description="Optional whitelist of pages to search within."
    )


class CitationOut(BaseModel):
    chunk_id: str
    page_number: int
    score: float
    excerpt: str


class QueryResponse(BaseModel):
    document_id: str
    question: str
    answer: str
    citations: list[CitationOut]
    input_tokens: int | None = None
    output_tokens: int | None = None
    created_at: datetime


class ChatMessageOut(BaseModel):
    role: str
    content: str
    created_at: datetime
    metadata: dict | None = None


class ChatHistoryOut(BaseModel):
    document_id: str
    history: list[ChatMessageOut]
