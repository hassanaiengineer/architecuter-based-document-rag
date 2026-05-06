from __future__ import annotations

import logging
from contextlib import asynccontextmanager

import asyncio
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from construction_rag.api.routes import admin, documents, queries
from construction_rag.core.config import get_settings
from construction_rag.core.errors import AppError
from construction_rag.core.logging import configure_logging
from construction_rag.core.paths import StoragePaths
from construction_rag.db.base import Base
from construction_rag.db.session import create_engine, create_session_factory

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    configure_logging(settings.log_level)

    paths = StoragePaths(settings.storage_dir)
    paths.ensure()

    engine = create_engine(settings.database_url)
    session_factory = create_session_factory(engine)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    app.state.settings = settings
    app.state.paths = paths
    app.state.engine = engine
    app.state.session_factory = session_factory
    app.state.ingestion_semaphore = asyncio.Semaphore(settings.max_concurrent_ingestions)
    yield
    await engine.dispose()


def create_app() -> FastAPI:
    app = FastAPI(title="Construction Document RAG", version="0.1.0", lifespan=lifespan)
    settings = get_settings()
    origins = settings.parsed_cors_origins()

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins or ["http://localhost:8501"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError):
        return JSONResponse(
            status_code=exc.status_code,
            content={"code": exc.code, "message": exc.message, "details": exc.details},
        )

    @app.exception_handler(Exception)
    async def unhandled_error_handler(request: Request, exc: Exception):
        logger.exception("Unhandled error: %s", exc)
        return JSONResponse(status_code=500, content={"code": "internal_error", "message": "Internal server error."})

    app.include_router(admin.router, prefix="/v1/admin", tags=["admin"])
    app.include_router(documents.router, prefix="/v1/documents", tags=["documents"])
    app.include_router(queries.router, prefix="/v1/documents", tags=["queries"])

    @app.get("/v1")
    async def root():
        return {"name": "construction-document-rag", "status": "ok"}

    return app


app = create_app()
