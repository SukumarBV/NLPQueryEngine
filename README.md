# AI-Powered NLP Query Engine

[![Python 3.11](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/)
[![Docker](https://img.shields.io/badge/docker-%230db7ed.svg?style=for-the-badge&logo=docker&logoColor=white)](https://www.docker.com/)
[![React](https://img.shields.io/badge/react-%2320232a.svg?style=for-the-badge&logo=react&logoColor=%2361DAFB)](https://reactjs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com/)

An intelligent full-stack application that lets users ask questions in plain English to query both structured SQL databases and unstructured documents at the same time.

## Description

This project provides a unified, natural-language interface over two very different kinds of data: a live PostgreSQL database and a collection of uploaded documents. It dynamically introspects any connected Postgres database to understand its schema, uses the Gemini API to translate questions into SQL, and performs semantic vector search over an indexed corpus of documents to answer questions the database alone can't.

## Key Features

* **Dynamic Schema Discovery** — introspects any connected PostgreSQL database (tables, columns, foreign keys) with no hard-coding.
* **LLM-Powered Text-to-SQL** — uses Google Gemini to translate natural-language questions into read-only SQL, with keyword/statement validation before execution.
* **Hybrid Search** — classifies each question as `SQL`, `DOCUMENT`, or `HYBRID`, and for hybrid questions actually runs both the SQL query *and* the document search, returning both result sets.
* **Document Ingestion & Indexing** — uploads PDFs/DOCX/TXT, chunks them, and embeds each chunk with the Gemini Embeddings API (no local ML model needed, so it runs comfortably on small hosts).
* **Query Caching & History** — repeated questions are served from an in-memory cache (`cache_hit: true`) and recent queries are available via `/api/query/history`.
* **Asynchronous RESTful API** — FastAPI backend with background-task document processing and job-status polling.
* **CSV Export** — export whatever results are on screen.
* **Single-container production build** — the same codebase builds either as a 3-container local dev stack (`docker-compose`) or as one combined image that serves the API and the built frontend from a single port, ready for a free-tier host like Koyeb.

## Technology Stack

* **Backend**: Python, FastAPI, SQLAlchemy, `google-genai` (Gemini API — text generation *and* embeddings)
* **Frontend**: React, JavaScript, HTML, CSS
* **Database**: PostgreSQL (bring your own — local, Koyeb Postgres, Neon, Supabase, etc.)
* **DevOps**: Docker, Docker Compose, Koyeb

> Note: earlier versions of this project used `sentence-transformers` + `faiss-cpu` (PyTorch) for embeddings. That stack alone is several hundred MB and doesn't fit in a 512MB free-tier container, so embeddings now go through the Gemini API instead. Your `GEMINI_API_KEY` is required for both SQL generation and document search.

## Getting Started (Local Development)

### Prerequisites

* Docker Desktop
* A [Gemini API key](https://aistudio.google.com/apikey)

### Setup

1. **Clone the repository**
   ```bash
   git clone <your-repository-url>
   cd NLPQueryEngine
   ```

2. **Configure environment variables**
   ```bash
   cp backend/.env.example backend/.env
   ```
   Open `backend/.env` and paste in your `GEMINI_API_KEY`. The default `DATABASE_URL` value matches the `db` service in `docker-compose.yml` and is only there for reference — the app itself connects to whichever database you enter in the UI.

3. **Start everything**
   ```bash
   docker compose up --build
   ```
   This starts Postgres, the FastAPI backend (`:8000`), and the React frontend (`:3000`).

4. **(Optional) Seed the database**
   ```bash
   docker exec -it nlpqueryengine-db-1 psql -U user -d company_db
   ```
   and paste in your own `CREATE TABLE` / `INSERT` statements (e.g. `employees`, `departments`).

5. Open **http://localhost:3000**, click **Connect & Analyze** with
   `postgresql://user:pass@db:5432/company_db`, optionally upload some documents, then ask a question.

## Usage

1. **Connect to Database** — enter a Postgres connection string and click "Connect & Analyze" to discover its schema.
2. **Upload Documents** *(optional)* — drag & drop PDF/DOCX/TXT files; they're chunked and embedded in the background.
3. **Ask a Question** — plain English, e.g. "How many employees are in Engineering?" or "Summarize Jane's latest performance review."
4. **Export** — download the current result set as CSV.

## Deploying to Koyeb (free tier)

Koyeb's free tier gives you **one** free web service (512MB RAM, 0.1 vCPU, no volumes, scales to zero after an hour of no traffic) plus an optional free Postgres database. Because you only get one free service, this repo includes a **root `Dockerfile`** that builds the React frontend and bundles it into the FastAPI container, so the whole app runs as a single service on a single port — no CORS, no second service needed.

### 1. Get a database

Pick one (all have free tiers):
* [Koyeb's managed Postgres](https://www.koyeb.com/docs) (free: 1GB RAM, 1GB storage, 50 active hours/month, auto-sleeps after 5 minutes idle)
* [Neon](https://neon.tech) or [Supabase](https://supabase.com) — fully-managed free Postgres that doesn't require a Koyeb-specific setup

Copy the connection string (it should look like `postgresql://user:password@host:port/dbname`). For safety, create a dedicated **read-only** database role/user for this app to use, since the query engine only ever runs `SELECT` statements but a read-only DB grant is a much stronger guarantee than application-level validation alone.

### 2. Push this repo to GitHub

Koyeb deploys from a Git repository (or a Docker image you push yourself).

### 3. Create the Koyeb service

1. In the Koyeb dashboard, click **Create Web Service** → **GitHub** and pick this repository.
2. Set **Builder** to **Dockerfile** and confirm the Dockerfile path is the root `Dockerfile` (not `backend/Dockerfile`).
3. Choose the **Free** instance type (Frankfurt or Washington, D.C. region).
4. Under **Ports**, expose port `8000` (or leave the default — the app reads Koyeb's `PORT` variable automatically).
5. Under **Environment variables**, add:
   * `GEMINI_API_KEY` = your key (mark it as a *Secret*)
   * `ALLOWED_ORIGINS` = `*` (default; fine for a single-origin deployment since the frontend is served from the same domain)
6. Click **Deploy**.

You do **not** need to set `DATABASE_URL` as an environment variable — the app asks for the connection string in the UI at runtime and stores it in memory for that instance.

### 4. Open the app

Once the deployment is healthy, Koyeb gives you a `*.koyeb.app` URL. Open it, connect your database, and start querying.

### Free-tier caveats to know about

* The free instance **scales to zero after ~1 hour of no traffic**, so the first request after idling will be slow (cold start) and any in-memory query cache/history/vector index resets.
* There are **no persistent volumes** on the free instance — uploaded documents and their embeddings live in memory only, for the current container's lifetime. Re-upload documents after a cold start if you need them again.
* 512MB RAM is enough for the app itself, but keep an eye on usage if you upload a lot of large documents at once (the embedding calls stream in batches of 100 chunks to avoid spiking memory).

### Redeploying with the CLI (alternative to the dashboard)

```bash
koyeb service create nlp-query-engine \
  --app nlp-query-engine \
  --git github.com/<you>/NLPQueryEngine \
  --git-branch main \
  --git-builder docker \
  --instance-type free \
  --regions fra \
  --ports 8000:http \
  --routes /:8000 \
  --env GEMINI_API_KEY={{secret.gemini-api-key}}
```

## Local single-container test (optional)

You can sanity-check the exact image Koyeb will build before deploying:

```bash
docker build -t nlp-query-engine .
docker run -p 8000:8000 -e GEMINI_API_KEY=your-key nlp-query-engine
```

Then open **http://localhost:8000** — both the UI and the API are served from that one port.

## API Overview

| Method | Path | Description |
| --- | --- | --- |
| `POST` | `/api/connect-database` | Discover schema for a connection string |
| `POST` | `/api/initialize-engine` | Initialize the query engine for a connection string |
| `POST` | `/api/upload-documents` | Upload documents for background ingestion |
| `GET` | `/api/ingestion-status/{job_id}` | Poll ingestion job status |
| `POST` | `/api/query` | Ask a natural-language question |
| `GET` | `/api/query/history` | Recent queries |
| `GET` | `/api/schema` | Current discovered schema |
| `GET` | `/api/health` | Liveness check |

## Future Improvements

* A dedicated vector database (e.g. pgvector, Weaviate) instead of an in-memory store, so documents survive restarts/cold starts.
* Support for more SQL dialects (MySQL, SQLite).
* User authentication and multi-tenancy.
* Redis-backed caching shared across instances.
