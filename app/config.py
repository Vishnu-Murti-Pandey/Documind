"""
Application configuration.

This file stores project-wide paths.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Full path to the Tesseract executable.
# Update this if Tesseract is installed elsewhere.
TESSERACT_CMD = Path(
    os.getenv(
        "TESSERACT_PATH",
        r"C:\Program Files\Tesseract-OCR\tesseract.exe",
    )
)

# ---------------------------------------------------
# Project Directories
# ---------------------------------------------------

ROOT_DIR = Path(__file__).resolve().parent.parent

DATA_DIR = ROOT_DIR / "data"

INPUT_DIR = DATA_DIR / "input"

IMAGE_DIR = DATA_DIR / "images"

# Create directories automatically

for directory in [
    INPUT_DIR,
    IMAGE_DIR,
]:
    directory.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------
# OpenAI
# ---------------------------------------------------

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

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

# ---------------------------------------------------
# MinIO
# ---------------------------------------------------

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

QDRANT_URL = os.getenv(
    "QDRANT_URL",
)

QDRANT_Sparse_Text_Embedding = os.getenv(
    "QDRANT_Sparse_Text_Embedding",
)

MINIO_SECURE = False