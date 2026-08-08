# Documind Backend

FastAPI backend for Documind, a document-aware chat application. It ingests PDF files, extracts and enriches text, figures, and tables, indexes the result for hybrid retrieval, streams grounded answers, and persists conversation history.

See [ARCHITECTURE.md](./ARCHITECTURE.md) for component boundaries, storage ownership, and end-to-end data flows.

## Features

- Streaming PDF ingestion with progress and cancellation
- Text, image, and table extraction from general PDF documents
- Semantic chunking and multimodal enrichment
- Dense and sparse indexing in Qdrant
- Retrieval, reranking, citations, figures, and tables
- Streaming chat responses over Server-Sent Events (SSE)
- Persistent conversations, messages, and rolling memory
- Object storage for uploaded files and extracted assets
- Stale-ingestion recovery and document cleanup

## Technology

- Python 3.11+
- FastAPI and Uvicorn
- PostgreSQL with async SQLAlchemy
- Qdrant
- MinIO
- OpenAI text, vision, and embedding APIs
- Unstructured, PyMuPDF, Tesseract, and pdf2image
- FastEmbed and sentence-transformers
- `uv` for dependency management

## Prerequisites

- Python 3.11 or newer
- [`uv`](https://docs.astral.sh/uv/)
- Docker with Docker Compose
- An OpenAI API key
- Tesseract OCR and Poppler available on the host

On Windows, set `TESSERACT_PATH` when Tesseract is not installed at the default location.

## Local setup

1. Install Python dependencies:

   ```powershell
   cd backend
   uv sync
   ```

2. Create `backend/.env.local`. The application loads `.env.local` by default, `.env.prod` when `ENVIRONMENT=production`, or the file named by `ENV_FILE`.

   ```dotenv
   ENVIRONMENT=development
   DEBUG=true

   POSTGRES_USER=documind
   POSTGRES_PASSWORD=change-me
   POSTGRES_DB=documind
   POSTGRES_PORT=5432
   DATABASE_URL=postgresql+asyncpg://documind:change-me@localhost:5432/documind
   DATABASE_ECHO=false

   MINIO_ROOT_USER=documind
   MINIO_ROOT_PASSWORD=change-me-too
   MINIO_PORT=9000
   MINIO_CONSOLE_PORT=9001
   MINIO_ENDPOINT=localhost:9000
   MINIO_ACCESS_KEY=documind
   MINIO_SECRET_KEY=change-me-too
   MINIO_BUCKET=documents
   MINIO_SECURE=false

   QDRANT_PORT=6333
   QDRANT_GRPC_PORT=6334
   QDRANT_URL=http://localhost:6333
   QDRANT_SPARSE_TEXT_EMBEDDING=Qdrant/bm25

   OPENAI_API_KEY=your-key
   OPENAI_TEXT_MODEL=gpt-4.1-mini
   OPENAI_VISION_MODEL=gpt-4.1-mini
   OPENAI_EMBEDDING_MODEL=text-embedding-3-small

   TESSERACT_PATH=C:\Program Files\Tesseract-OCR\tesseract.exe
   CONVERSATION_HISTORY_LIMIT=10
   MAX_UPLOAD_SIZE_MB=50
   ```

3. Start PostgreSQL, MinIO, and Qdrant:

   ```powershell
   docker compose -f docker-compose.local.yml up -d
   ```

4. Start the API:

   ```powershell
   uv run uvicorn app.main:app --reload
   ```

The API is available at `http://127.0.0.1:8000`, with interactive documentation at `http://127.0.0.1:8000/docs`.

## Configuration

| Variable | Purpose | Default |
| --- | --- | --- |
| `ENV_FILE` | Explicit dotenv file; takes priority over `ENVIRONMENT` | unset |
| `ENVIRONMENT` | Chooses local or production configuration | `development` |
| `DATABASE_URL` | Async PostgreSQL connection URL | required |
| `MINIO_ENDPOINT` | MinIO host and port | `localhost:9000` |
| `MINIO_ACCESS_KEY` / `MINIO_SECRET_KEY` | MinIO application credentials | required |
| `MINIO_BUCKET` | Uploaded document and asset bucket | `research-papers` |
| `QDRANT_URL` | Qdrant HTTP endpoint | required |
| `QDRANT_SPARSE_TEXT_EMBEDDING` | Sparse embedding model | provider configuration |
| `OPENAI_API_KEY` | Model provider credential | required |
| `OPENAI_TEXT_MODEL` | Answer-generation model | `gpt-4.1-mini` |
| `OPENAI_VISION_MODEL` | Figure/table enrichment model | `gpt-4.1-mini` |
| `OPENAI_EMBEDDING_MODEL` | Dense embedding model | `text-embedding-3-small` |
| `CONVERSATION_HISTORY_LIMIT` | Recent messages supplied to conversation memory | `10` |
| `MAX_UPLOAD_SIZE_MB` | Maximum accepted PDF size | `50` |

Do not commit real credentials. The checked-in ignore rules should keep local environment files out of source control.

## API overview

All application endpoints use the `/api` prefix.

| Area | Important endpoints |
| --- | --- |
| Health | `GET /api/health`, `GET /api/health/database` |
| Ingestion | `POST /api/ingestion/stream`, `POST /api/ingestion/{document_id}/cancel` |
| Documents | `GET /api/documents`, `GET /api/documents/{document_id}`, `DELETE /api/documents/{document_id}` |
| Chat | `POST /api/chat`, `POST /api/chat/stream` |
| Conversations | list, read, rename, delete, and paginated message endpoints below `/api/conversations` |
| Assets | `GET /api/assets/{object_path}` |

Streaming endpoints return SSE events. Clients must continue reading until a terminal `done`, `error`, or cancellation event is received.

## Development commands

```powershell
# Run tests
uv run pytest

# Start with an explicit environment file
$env:ENV_FILE='.env.local'
uv run uvicorn app.main:app --reload

# Stop local infrastructure without deleting volumes
docker compose -f docker-compose.local.yml down
```

## Data and generated files

- `data/input/` holds local ingestion working files.
- `data/images/` holds extracted image working files.
- PostgreSQL, MinIO, and Qdrant use named Docker volumes in local development.
- The API creates missing PostgreSQL tables during application startup.

## Troubleshooting

- **Database health fails:** verify the `DATABASE_URL` credentials match the Docker Compose PostgreSQL variables.
- **Assets cannot be loaded:** check the MinIO endpoint, credentials, bucket, and port `9000`; the console runs on `9001`.
- **OCR or PDF conversion fails:** verify Tesseract and Poppler are installed and reachable.
- **Hugging Face rate-limit warning:** set `HF_TOKEN` in the process environment for authenticated model downloads.
- **An ingestion remains processing:** cancellation must be sent to the cancellation endpoint. On subsequent document listing, stale processing records are recovered according to the backend policy.
- **CORS failure:** local CORS currently allows `http://localhost:3000`; update `app/main.py` for another frontend origin.

## Repository layout

```text
backend/
├── app/
│   ├── api/             # FastAPI routes and request/response schemas
│   ├── services/        # Chat, conversation, and document orchestration
│   ├── parser/          # PDF parsing and element extraction
│   ├── preprocessing/   # Ingestion preparation
│   ├── enrichment/      # Figure captions and table summaries
│   ├── chunking/        # Semantic chunk construction
│   ├── embedding/       # Dense/sparse embedding adapters
│   ├── retrieval/       # Hybrid retrieval pipeline
│   ├── reranking/       # Result reranking
│   ├── generation/      # Prompting and answer generation
│   ├── repositories/    # Persistence access
│   ├── storage/         # MinIO integration
│   ├── vectorstore/     # Qdrant integration
│   └── db/              # SQLAlchemy models and sessions
├── tests/
├── docker/
├── docker-compose.local.yml
└── pyproject.toml
```
