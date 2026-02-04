# RAGonWeb

Retrieval-Augmented Generation (RAG) API for crawling and indexing web content and serving semantic search + LLM answers.

This repository implements a FastAPI service that crawls a website, generates embeddings, stores vectors in Milvus, and answers queries using retrieved context and an LLM (Gemini client).

---

## Contents
- `main.py` — entry point to run the FastAPI server
- `src/api` — FastAPI app and route modules
- `src/crawler` — web crawler used for ingestion
- `src/embeddings` — embeddings generation wrapper
- `src/database` — Milvus client and data models
- `Dockerfile`, `docker-compose.yml` — dockerized deployment
- `requirements.txt` — python dependencies

---

## Quickstart (Local, Python)

1. Create a virtual environment and activate it:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Provide runtime environment variables. Create a `.env` file in the project root or export variables in your shell. Minimal example shown in the next section.

4. Run the API server:

```bash
python main.py
```

The server will start with the host and port defined in the config (`API_HOST`, `API_PORT`). By default the app listens on `0.0.0.0:8000`.

---

## Quickstart (Docker)

If you prefer Docker, the repository includes a `Dockerfile` and `docker-compose.yml` (if you use `docker-compose` to orchestrate Milvus/MinIO etc.). Example:

```bash
# build the image
docker build -t ragonweb:local .

# run with docker-compose (if your compose file configures required services)
docker-compose up --build
```

Make sure dependent services (Milvus, MinIO if used) are reachable and configured via environment variables.

---

## Environment Variables (.env example)

Create a `.env` file with the following keys (values shown are typical defaults or examples):

```dotenv
# Milvus
MILVUS_HOST=localhost
MILVUS_PORT=19530
MILVUS_DB_NAME=barco
MILVUS_COLLECTION_NAME=web_data

# API
API_HOST=0.0.0.0
API_PORT=8000

# Web crawler defaults
BASE_URL=https://www.barco.com
CRAWL_MAX_DEPTH=5
CRAWL_MAX_URLS=1000
CRAWL_TIMEOUT=30
REQUEST_DELAY=1.0
USER_AGENT=RAGonWebBot/1.0

# Embeddings & LLM
EMBEDDING_MODEL=all-MiniLM-L6-v2
EMBEDDING_DIMENSION=384
GOOGLE_API_KEY=your_google_api_key_here

# Batch and memory
BATCH_SIZE=32
```

Notes:
- `GOOGLE_API_KEY` is used by the `GeminiClient` wrapper inside `src/llm` to call the LLM. Set a valid key or ensure the environment provider is configured.
- The app uses `pydantic-settings` to load `.env` by default.

---

## API Reference

All endpoints are mounted under `/api/v1`.

1) Health
- Path: `GET /api/v1/health`
- Description: Checks API and database (Milvus) health. Returns collection stats if available.
- Response: JSON with `status`, `database`, and `collection_stats` or 503 if Milvus is unavailable.

Example:

```bash
curl -X GET http://localhost:8000/api/v1/health
```

2) Ingest
- Path: `POST /api/v1/ingest`
- Description: Starts an ingestion (background) task that crawls the `base_url`, chunks documents, computes embeddings, and indexes vectors in Milvus.
- Request body (JSON):
  - `base_url` (string, optional) — root URL to crawl (defaults to config.BASE_URL)
  - `max_depth` (int, optional) — crawl depth
  - `max_urls` (int, optional) — max number of URLs to visit
  - `chunk_size` (int, optional) — characters per chunk (default 1000)

- Response: 202-style acceptance with `status`, `message`, and `task_id`.

Example request:

```bash
curl -X POST http://localhost:8000/api/v1/ingest \
  -H "Content-Type: application/json" \
  -d '{"base_url": "https://www.barco.com", "max_depth": 2, "max_urls": 200}'
```

Notes:
- Ingestion runs as a background task; the endpoint immediately returns an acceptance response and continues processing asynchronously.
- Logs and progress appear in the application logs (`logs/app.log` by default if configured).

3) Search (Semantic + RAG)
- Path: `POST /api/v1/search`
- Description: Performs semantic search against Milvus and uses the LLM to generate a contextualized answer (retrieval-augmented generation).
- Request body (JSON):
  - `query` (string) — the user query
  - `top_k` (int, optional, default 5) — number of results to retrieve

- Response: JSON matching `SearchResponse` with fields:
  - `answer` — LLM-generated answer using retrieved documents
  - `results` — list of `SearchResult` objects (content, content_url, distance, similarity_score)

Example request:

```bash
curl -X POST http://localhost:8000/api/v1/search \
  -H "Content-Type: application/json" \
  -d '{"query": "How do Barco projectors handle 4K input?", "top_k": 3}'
```

---

## Logging

Application logging is configured via `logger_config.py`. By default there is a `logs/app.log` file in the repository; check that file for ingestion progress, errors, and other diagnostic output.

---

## Architecture & Implementation Notes

- The service uses FastAPI with an application factory `src/api/app.py`.
- `src/crawler/crawler.py` implements a basic web crawler used by the ingest pipeline.
- `src/embeddings/embeddings.py` wraps an embeddings generator. A singleton pattern is used for memory efficiency.
- `src/database/milvus_client.py` is the Milvus integration layer; collections and vector insert/search live there.
- `src/llm/gemini_client.py` wraps the LLM API call used to generate answers from retrieved documents.

Performance considerations:
- Embeddings and the LLM can be memory- and CPU/GPU-intensive. Tune `BATCH_SIZE` and the singleton embedder usage as needed.
- Milvus should be provisioned with enough memory and disk for the expected vector dataset.

---

## Troubleshooting

- If health checks fail with a Milvus connection error, verify `MILVUS_HOST` and `MILVUS_PORT` and that Milvus is running.
- If embeddings or the LLM fail, confirm `EMBEDDING_MODEL` and `GOOGLE_API_KEY` (or alternative provider credentials) are set.
- For crawler-related failures, check network access and `BASE_URL`.

---

