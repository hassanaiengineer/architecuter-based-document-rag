from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class StoragePaths:
    base_dir: Path

    @property
    def uploads_dir(self) -> Path:
        return self.base_dir / "uploads"

    @property
    def pages_dir(self) -> Path:
        return self.base_dir / "pages"

    @property
    def extracted_text_dir(self) -> Path:
        return self.base_dir / "extracted_text"

    @property
    def structured_dir(self) -> Path:
        return self.base_dir / "structured"

    @property
    def indexes_dir(self) -> Path:
        return self.base_dir / "indexes"

    def ensure(self) -> None:
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.uploads_dir.mkdir(parents=True, exist_ok=True)
        self.pages_dir.mkdir(parents=True, exist_ok=True)
        self.extracted_text_dir.mkdir(parents=True, exist_ok=True)
        self.structured_dir.mkdir(parents=True, exist_ok=True)
        self.indexes_dir.mkdir(parents=True, exist_ok=True)

