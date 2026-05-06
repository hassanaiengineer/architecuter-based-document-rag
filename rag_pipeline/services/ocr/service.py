from __future__ import annotations

import logging
from pathlib import Path

from construction_rag.core.config import Settings
from construction_rag.services.ocr.google_vision import GoogleVisionOcr
from construction_rag.services.ocr.models import PageText
from construction_rag.services.ocr.pdf_text import PdfTextExtractor

logger = logging.getLogger(__name__)


class OcrService:
    def __init__(self, settings: Settings):
        self._settings = settings
        self._text_extractor = PdfTextExtractor()
        self._google_ocr: GoogleVisionOcr | None = None

        if settings.ocr_mode == "google_vision":
            self._google_ocr = GoogleVisionOcr(credentials_path=settings.google_application_credentials)
        elif settings.ocr_mode == "auto" and settings.google_application_credentials:
            self._google_ocr = GoogleVisionOcr(credentials_path=settings.google_application_credentials)

    def extract_pages(self, pdf_path: Path) -> list[PageText]:
        if self._settings.ocr_mode == "google_vision":
            assert self._google_ocr is not None
            return self._google_ocr.extract(pdf_path)

        pages = self._text_extractor.extract(pdf_path)
        if self._settings.ocr_mode == "text_only":
            return pages

        # auto mode: fallback when most pages have little/no text
        if self._google_ocr is None:
            return pages

        empty_pages = sum(1 for p in pages if len(p.text.strip()) < 40)
        ratio_empty = empty_pages / max(1, len(pages))
        if ratio_empty < 0.5:
            logger.info("OCR auto mode: embedded text looks usable (empty_ratio=%.2f)", ratio_empty)
            return pages

        logger.info("OCR auto mode: falling back to Google Vision (empty_ratio=%.2f)", ratio_empty)
        return self._google_ocr.extract(pdf_path)
