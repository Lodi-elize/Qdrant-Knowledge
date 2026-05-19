# Qdrant Knowledge Assistant

A customer-facing RAG knowledge assistant for product documentation. Administrators upload official documents, users ask questions against a selected product line and version, and the backend retrieves scoped chunks from Qdrant before generating an answer with an OpenAI-compatible chat model such as DeepSeek.

## Features

- Customer chat UI built with React and Vite.
- FastAPI backend with generated OpenAPI docs.
- Admin-only document upload for official product documents.
- Product-line/product-version knowledge-base isolation.
- Qdrant vector storage with metadata-filtered retrieval.
- DeepSeek/OpenAI-compatible chat generation.
- Local deterministic embeddings for offline development and tests.
- Markdown rendering for model answers.
- Collapsed source evidence panel by default.

## Architecture

```text
frontend/
  React chat and admin upload UI

backend/
  FastAPI API layer
  ingestion service -> parse, chunk, embed, upsert
  scoped retrieval service -> requires product_line + product_version
  generation service -> local or OpenAI-compatible chat model

qdrant/
  Stores document chunks and vectors with product/version metadata
```

The query path is intentionally scoped:

1. User selects `product_line` and `product_version`.
2. Backend builds a `KnowledgeBaseScope`.
3. Query routes call `ScopedRetrievalService`.
4. Qdrant search applies both metadata filters.
5. The answer response includes `answer`, `sources`, `grounded_summary`, and supplemental metadata.

Routes and generation code should not query Qdrant directly.

## Requirements

- Python 3.11+
- Node.js 20+
- Docker Desktop
- A DeepSeek API key if using real model generation

## Setup

```powershell
cd E:\aiAgent
py -m venv .venv
.\.venv\Scripts\python -m pip install -e .\backend[test]
npm --prefix frontend install
docker compose up -d qdrant
```

Create `.env` from `.env.example`:

```powershell
Copy-Item .env.example .env
```

Do not commit `.env`; it may contain API keys.

## Environment

Local/offline mode:

```env
APP_ADMIN_SECRET=change-me
APP_ADMIN_COOKIE_SECURE=false
APP_VECTOR_BACKEND=qdrant
APP_QDRANT_URL=http://127.0.0.1:6333
APP_QDRANT_COLLECTION=product_docs
APP_MODEL_PROVIDER=local
APP_EMBEDDING_PROVIDER=local
```

DeepSeek chat mode:

```env
APP_ADMIN_SECRET=change-me
APP_ADMIN_COOKIE_SECURE=false
APP_VECTOR_BACKEND=qdrant
APP_QDRANT_URL=http://127.0.0.1:6333
APP_QDRANT_COLLECTION=product_docs
APP_MODEL_PROVIDER=openai-compatible
APP_EMBEDDING_PROVIDER=local
APP_OPENAI_CHAT_API_BASE=https://api.deepseek.com
APP_OPENAI_CHAT_API_KEY=<your-deepseek-api-key>
APP_CHAT_MODEL=deepseek-v4-flash
```

DeepSeek is used for chat generation only. Embeddings default to local deterministic embeddings so the app does not call an unsupported DeepSeek embedding endpoint.

## Run

Start Qdrant:

```powershell
docker compose up -d qdrant
```

Start backend:

```powershell
.\.venv\Scripts\python -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 9090 --reload
```

Start frontend:

```powershell
npm --prefix frontend run dev -- --host 127.0.0.1
```

Open:

- Web UI: http://127.0.0.1:8080
- API docs: http://127.0.0.1:9090/docs
- Qdrant dashboard: http://127.0.0.1:6333/dashboard

## Usage

1. Open the web UI.
2. Enter the admin secret in the admin panel.
3. Set a product line and product version.
4. Upload `.txt`, `.md`, or `.pdf` official documentation.
5. Ask questions in the chat panel.

The answer panel renders Markdown. Source evidence is collapsed by default and can be expanded when needed.

## API Examples

Query:

```powershell
Invoke-RestMethod -Method Post http://127.0.0.1:9090/api/query `
  -ContentType "application/json" `
  -Body '{"product_line":"Delta","product_version":"v1","question":"What is the refund policy?"}'
```

Upload:

```powershell
curl.exe -X POST "http://127.0.0.1:9090/api/admin/upload?product_line=Delta&product_version=v1" `
  -H "X-Admin-Secret: change-me" `
  -F "file=@.\docs\delta-v1.md"
```

## Verification

```powershell
.\.venv\Scripts\python -m pytest backend
npm --prefix frontend test
npm --prefix frontend run build
```

Important coverage:

- Admin-only upload.
- Response schema.
- Scoped retrieval facade.
- Cross-version leakage prevention.
- Qdrant repository filtering through qdrant-client.

## Troubleshooting

Docker Hub pull failures can often be fixed by configuring a registry mirror in Docker Desktop. This project has been tested with Qdrant `1.12.4`.

If Docker is unavailable, the repository-level Qdrant behavior can still be checked without a running container:

```powershell
.\.venv\Scripts\python -m pytest backend\tests\test_qdrant_repository.py
```

That test uses qdrant-client's local `:memory:` Qdrant engine.

If Qdrant requests return `502` from the backend while direct browser/PowerShell access works, clear proxy variables when starting the backend:

```powershell
$env:NO_PROXY="127.0.0.1,localhost"
$env:no_proxy="127.0.0.1,localhost"
$env:HTTP_PROXY=""
$env:HTTPS_PROXY=""
```

## Repository Notes

- `.env`, virtual environments, build output, caches, and dependency folders are ignored.
- Do not commit API keys or admin secrets.
- The intended GitHub remote is `https://github.com/Lodi-elize/Qdrant-Knowledge.git`.
