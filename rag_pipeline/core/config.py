from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Literal

from dotenv import load_dotenv
from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_ignore_empty=True, extra="ignore")

    app_env: Literal["local", "staging", "prod"] = Field(default="local", alias="APP_ENV")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    host: str = Field(default="0.0.0.0", alias="HOST")
    port: int = Field(default=8000, alias="PORT")
    cors_origins: str = Field(default="", alias="CORS_ORIGINS")

    storage_dir: Path = Field(default=Path("./data"), alias="STORAGE_DIR")
    database_url: str = Field(default="sqlite+aiosqlite:///./data/app.db", alias="DATABASE_URL")

    # OCR
    ocr_mode: Literal["auto", "text_only", "google_vision"] = Field(default="auto", alias="OCR_MODE")
    google_application_credentials: Path | None = Field(
        default=None, alias="GOOGLE_APPLICATION_CREDENTIALS"
    )

    # Retrieval
    embedding_model: str = Field(default="text-embedding-3-small", alias="EMBEDDING_MODEL")
    rerank_mode: Literal["off", "bm25"] = Field(default="bm25", alias="RERANK_MODE")
    top_k_default: int = Field(default=6, alias="TOP_K_DEFAULT")
    rerank_top_n: int = Field(default=20, alias="RERANK_TOP_N")

    # LLM
    llm_provider: Literal["anthropic", "openai"] = Field(default="anthropic", alias="LLM_PROVIDER")
    llm_model: str | None = Field(default=None, alias="LLM_MODEL")
    anthropic_api_key: SecretStr | None = Field(default=None, alias="ANTHROPIC_API_KEY")
    openai_api_key: SecretStr | None = Field(default=None, alias="OPENAI_API_KEY")

    # Admin
    admin_api_key: SecretStr | None = Field(default=None, alias="ADMIN_API_KEY")

    # In-process ingestion runner
    max_concurrent_ingestions: int = 2

    def parsed_cors_origins(self) -> list[str]:
        raw = (self.cors_origins or "").strip()
        if not raw:
            return []
        return [o.strip() for o in raw.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    load_dotenv(override=False)
    return Settings()
