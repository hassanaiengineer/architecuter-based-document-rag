from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class PageText:
    page_number: int
    text: str
    method: str  # text|ocr

