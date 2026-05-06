from __future__ import annotations

import io
import logging
import os
from pathlib import Path

from google.cloud import vision
from pdf2image import convert_from_path

from construction_rag.core.errors import ConfigError, ProcessingError
from construction_rag.services.ocr.models import PageText

logger = logging.getLogger(__name__)


class GoogleVisionOcr:
    def __init__(self, *, credentials_path: Path | None):
        if credentials_path is None:
            raise ConfigError(
                "Google Vision OCR requires GOOGLE_APPLICATION_CREDENTIALS to be set."
            )
        os.environ.setdefault("GOOGLE_APPLICATION_CREDENTIALS", str(credentials_path))
        self._client = vision.ImageAnnotatorClient()

    def _pdf_to_images(self, pdf_path: Path, *, dpi: int) -> list[bytes]:
        try:
            images = convert_from_path(str(pdf_path), dpi=dpi)
        except Exception as exc:  # pragma: no cover
            raise ProcessingError(f"PDF to image conversion failed: {exc}") from exc
        output: list[bytes] = []
        for img in images:
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            output.append(buf.getvalue())
        return output

    def extract(self, pdf_path: Path, *, dpi: int = 220) -> list[PageText]:
        images = self._pdf_to_images(pdf_path, dpi=dpi)
        pages: list[PageText] = []
        for index, image_bytes in enumerate(images):
            image = vision.Image(content=image_bytes)
            resp = self._client.document_text_detection(image=image)
            if resp.error.message:
                raise ProcessingError(f"OCR error on page {index + 1}: {resp.error.message}")
            text = (resp.full_text_annotation.text or "").strip()
            pages.append(PageText(page_number=index + 1, text=text, method="ocr"))
        logger.info("OCR extracted text for %s pages", len(pages))
        return pages

