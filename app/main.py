"""
FastAPI application entry point.
"""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.assets import (
    router as assets_router,
)
from app.api.routes.health import (
    router as health_router,
)
from app.api.routes.chat import (
    router as chat_router,
)
from app.db.session import (
    create_database_tables,
    dispose_engine,
)
from app.api.routes.conversations import (
    router as conversations_router,
)


@asynccontextmanager
async def lifespan(
    app: FastAPI,
) -> AsyncGenerator[None, None]:
    """
    FastAPI startup and shutdown lifecycle.
    """

    # Create PostgreSQL tables that do not already exist.
    await create_database_tables()

    yield

    # Close database connections cleanly.
    await dispose_engine()


app = FastAPI(
    title="Multimodal RAG API",
    version="1.0.0",
    lifespan=lifespan,
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(
    chat_router,
    prefix="/api",
)

app.include_router(
    assets_router,
    prefix="/api",
)

app.include_router(
    conversations_router,
    prefix="/api",
)

app.include_router(
    health_router,
    prefix="/api",
)


@app.get("/")
async def root():
    return {
        "message": "Multimodal RAG API is running",
    }
