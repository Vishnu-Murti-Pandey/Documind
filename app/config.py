"""
Application configuration.

Loads the appropriate environment file and exposes
all application configuration in one place.
"""

import os
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from dotenv import load_dotenv

# ============================================================
# Project Root
# ============================================================

ROOT_DIR = Path(__file__).resolve().parent.parent


# ============================================================
# Environment Loading
# ============================================================

def _load_environment() -> None:
    """
    Load the correct dotenv file.

    Priority:

    1. ENV_FILE
    2. ENVIRONMENT
    """

    explicit_env = os.getenv("ENV_FILE")

    if explicit_env:

        env_path = Path(explicit_env)

        if not env_path.is_absolute():
            env_path = ROOT_DIR / env_path

        load_dotenv(
            env_path,
            override=False,
        )

        return

    environment = os.getenv(
        "ENVIRONMENT",
        "development",
    ).lower()

    env_file = (
        ".env.prod"
        if environment in {
            "prod",
            "production",
        }
        else ".env.local"
    )

    load_dotenv(
        ROOT_DIR / env_file,
        override=False,
    )


_load_environment()


# ============================================================
# General
# ============================================================

ENVIRONMENT = os.getenv(
    "ENVIRONMENT",
    "development",
)

DEBUG = (
    os.getenv(
        "DEBUG",
        "false",
    ).lower()
    == "true"
)

ALLOWED_ORIGINS = [
    origin.strip().rstrip("/")
    for origin in os.getenv(
        "ALLOWED_ORIGINS",
        "http://localhost:3000",
    ).split(",")
    if origin.strip()
]

CORS_ORIGIN_REGEX = os.getenv(
    "CORS_ORIGIN_REGEX",
) or None


# ============================================================
# Project Directories
# ============================================================

DATA_DIR = ROOT_DIR / "data"

INPUT_DIR = DATA_DIR / "input"

IMAGE_DIR = DATA_DIR / "images"

for directory in (
    INPUT_DIR,
    IMAGE_DIR,
):
    directory.mkdir(
        parents=True,
        exist_ok=True,
    )


# ============================================================
# OCR
# ============================================================

TESSERACT_CMD = Path(
    os.getenv(
        "TESSERACT_PATH",
        r"C:\Program Files\Tesseract-OCR\tesseract.exe",
    )
)


# ============================================================
# OpenAI
# ============================================================

OPENAI_API_KEY = os.getenv(
    "OPENAI_API_KEY",
)

TEXT_MODEL = os.getenv(
    "OPENAI_TEXT_MODEL",
    "gpt-4.1-mini",
)

VISION_MODEL = os.getenv(
    "OPENAI_VISION_MODEL",
    "gpt-4.1-mini",
)

EMBEDDING_MODEL = os.getenv(
    "OPENAI_EMBEDDING_MODEL",
    "text-embedding-3-small",
)


# ============================================================
# PostgreSQL
# ============================================================

def _normalize_database_url(value: str | None) -> str | None:
    """Convert provider PostgreSQL URLs into SQLAlchemy asyncpg URLs."""

    if not value:
        return None

    if value.startswith("postgres://"):
        value = "postgresql://" + value.removeprefix("postgres://")

    if value.startswith("postgresql://"):
        value = "postgresql+asyncpg://" + value.removeprefix("postgresql://")

    parts = urlsplit(value)
    query = dict(parse_qsl(parts.query, keep_blank_values=True))
    sslmode = query.pop("sslmode", None)
    query.pop("channel_binding", None)

    if sslmode and "ssl" not in query:
        query["ssl"] = sslmode

    return urlunsplit(
        (parts.scheme, parts.netloc, parts.path, urlencode(query), parts.fragment)
    )


DATABASE_URL = _normalize_database_url(os.getenv("DATABASE_URL"))

DATABASE_ECHO = (
    os.getenv(
        "DATABASE_ECHO",
        "false",
    ).lower()
    == "true"
)

DATABASE_POOL_SIZE = int(os.getenv("DATABASE_POOL_SIZE", "5"))
DATABASE_MAX_OVERFLOW = int(os.getenv("DATABASE_MAX_OVERFLOW", "10"))


# ============================================================
# MinIO
# ============================================================

MINIO_ENDPOINT = os.getenv(
    "MINIO_ENDPOINT",
    "localhost:9000",
)

MINIO_ACCESS_KEY = os.getenv(
    "MINIO_ACCESS_KEY",
)

MINIO_SECRET_KEY = os.getenv(
    "MINIO_SECRET_KEY",
)

MINIO_BUCKET = os.getenv(
    "MINIO_BUCKET",
    "research-papers",
)

MINIO_SECURE = (
    os.getenv(
        "MINIO_SECURE",
        "false",
    ).lower()
    == "true"
)

MINIO_REGION = os.getenv(
    "MINIO_REGION",
) or None


# ============================================================
# Qdrant
# ============================================================

QDRANT_URL = os.getenv(
    "QDRANT_URL",
)

QDRANT_API_KEY = os.getenv(
    "QDRANT_API_KEY",
) or None

QDRANT_TIMEOUT_SECONDS = int(
    os.getenv(
        "QDRANT_TIMEOUT_SECONDS",
        "30",
    )
)

QDRANT_SPARSE_TEXT_EMBEDDING = os.getenv(
    "QDRANT_SPARSE_TEXT_EMBEDDING",
)


# ============================================================
# Redis (Phase 3)
# ============================================================

REDIS_URL = os.getenv(
    "REDIS_URL",
    "redis://localhost:6379",
)

# ============================================================
# Conversation Memory
# ============================================================

CONVERSATION_HISTORY_LIMIT = int(
    os.getenv(
        "CONVERSATION_HISTORY_LIMIT",
        "10",
    )
)

# ============================================================
# Document Ingestion
# ============================================================

MAX_UPLOAD_SIZE_MB = int(
    os.getenv(
        "MAX_UPLOAD_SIZE_MB",
        "50",
    )
)

MAX_UPLOAD_SIZE_BYTES = (
    MAX_UPLOAD_SIZE_MB * 1024 * 1024
)
