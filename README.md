# AI-Powered NLP Query Engine

[![Python 3.11](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/)
[![Docker](https://img.shields.io/badge/docker-%230db7ed.svg?style=for-the-badge&logo=docker&logoColor=white)](https://www.docker.com/)
[![React](https://img.shields.io/badge/react-%2320232a.svg?style=for-the-badge&logo=react&logoColor=%2361DAFB)](https://reactjs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com/)

An intelligent full-stack application that lets users ask questions in plain English to query both structured SQL databases and unstructured documents at the same time.

## Description

This project provides a unified, natural-language interface over structured and unstructured data — with **zero setup required to try it**. Open the app and pick one of three ways in: connect your own PostgreSQL database, drag in your own files (CSV/XLSX/PDF/DOCX/TXT), or click "Use Demo" for an instant, preloaded sample dataset. Whichever you choose, the same engine dynamically discovers the SQL schema, uses the Gemini API to translate questions into SQL, and performs semantic vector search over any ingested documents to answer questions the database alone can't.

## Screenshots

This README doesn't ship with pre-rendered screenshots (none were generated for this build), but here's what to capture once you have it running locally or on Koyeb — drop the images into a `docs/` folder and reference them below:

| Suggested file | What to capture |
| --- | --- |
| `docs/landing.png` | The "Choose Your Data Source" screen with all three cards |
| `docs/demo-query.png` | A query + hybrid result on the Demo dataset |
| `docs/upload-files.png` | The Upload Files screen mid-drag, with a file grouped under "Structured Data" and another under "Documents" |
| `docs/postgres-schema.png` | The discovered schema view after connecting PostgreSQL |
| `docs/results-export.png` | A results table with the "Export as CSV" button visible |

```markdown
![Choose Your Data Source](docs/landing.png)
![Demo query result](docs/demo-query.png)
```

## Choose Your Data Source

| | |
|---|---|
| 🗄 **Connect PostgreSQL** | Bring your own database. Schema is introspected automatically and natural-language → SQL just works. |
| 📁 **Upload Files** | Drop in PDFs, Word docs, CSVs or Excel workbooks. Every CSV and every worksheet in an XLSX becomes its own queryable SQL table (via an in-memory SQLite engine); PDFs/DOCX/TXT are chunked and embedded for semantic search. Mix and match — e.g. `sales.csv` + `employees.xlsx` + `report.pdf` together. |
| 🚀 **Try Demo** | A realistic, preloaded sample dataset (employees, departments, customers, products, orders, sales — ~500 rows) with no download, no API call, and no setup. Ask a question within seconds. |

You can also layer document uploads *on top of* PostgreSQL or the demo dataset (e.g. connect Postgres, then upload a PDF report) — hybrid search will combine both automatically.

## Key Features

* **Three zero-friction entry points** — PostgreSQL, file upload, or an instant offline demo dataset, unified behind one data-source abstraction (`BaseSQLDataSource` → `PostgresDataSource` / `SQLiteUploadDataSource` / `DemoDataSource`) so the query engine never needs to know which one is active.
* **Dynamic Schema Discovery** — introspects any connected SQL backend (tables, columns, foreign keys) with no hard-coding, whether it's Postgres or a spreadsheet-derived SQLite table.
* **LLM-Powered Text-to-SQL** — uses Google Gemini to translate natural-language questions into read-only SQL (dialect-aware for Postgres vs. SQLite), with keyword/statement validation before execution.
* **CSV/XLSX → SQL tables** — CSVs and every worksheet in an XLSX workbook are loaded into an in-memory SQLite database via pandas, so you can ask "top 10 customers" or "average sales by region" without ever touching a database.
* **Hybrid Search** — classifies each question as `SQL`, `DOCUMENT`, or `HYBRID`, and for hybrid questions actually runs both the SQL query *and* the document search, returning both result sets (e.g. "Which department has the highest payroll, and what does report.pdf say about it?").
* **Document Ingestion & Indexing** — uploads PDFs/DOCX/TXT, chunks them, and embeds each chunk with the Gemini Embeddings API (no local ML model needed, so it runs comfortably on small hosts).
* **Query Caching & History** — repeated questions are served from an in-memory cache (`cache_hit: true`) and recent queries are available via `/api/query/history`.
* **Asynchronous RESTful API** — FastAPI backend with background-task document processing and job-status polling.
* **CSV Export** — export whatever results are on screen.
* **Single-container production build** — the same codebase builds either as a 3-container local dev stack (`docker-compose`) or as one combined image that serves the API and the built frontend from a single port, ready for a free-tier host like Koyeb.

## Technology Stack

* **Backend**: Python, FastAPI, SQLAlchemy, `google-genai` (Gemini API — text generation *and* embeddings), pandas + openpyxl (CSV/XLSX ingestion)
* **Frontend**: React, JavaScript, HTML, CSS
* **Database**: PostgreSQL (bring your own — local, Koyeb Postgres, Neon, Supabase, etc.), or zero-setup SQLite for uploaded files / the demo dataset
* **DevOps**: Docker, Docker Compose, Koyeb

> Note: earlier versions of this project used `sentence-transformers` + `faiss-cpu` (PyTorch) for embeddings. That stack alone is several hundred MB and doesn't fit in a 512MB free-tier container, so embeddings now go through the Gemini API instead. Your `GEMINI_API_KEY` is required for both SQL generation and document search.

### Architecture: pluggable data sources

The query engine talks to a `BaseSQLDataSource` interface (`backend/api/services/datasources/`), not to PostgreSQL directly, so the exact same Text-to-SQL pipeline and validation logic works no matter which mode is active:

```
BaseSQLDataSource (abstract: get_schema(), execute(sql), describe())
├── PostgresDataSource      — your own PostgreSQL connection
└── SQLiteDataSource        — shared SQLite introspection/execution logic
    ├── SQLiteUploadDataSource — CSV/XLSX uploads → generated SQLite tables
    └── DemoDataSource         — preloaded offline sample dataset
```

`EngineManager` (`backend/api/services/engine_manager.py`) is a single process-wide object that owns the shared document store and whichever data source is currently active, and knows how to switch between them (`connect_postgres`, `use_demo`, `activate_uploads`, `reset`). Document search always uses the same shared store regardless of which SQL data source is active, which is what makes hybrid queries like "compare employee counts with report findings" work across a Postgres connection *and* an uploaded PDF at the same time.

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

5. Open **http://localhost:3000**. Click **🚀 Try Demo** for an instant sample dataset, **📁 Upload Files** to try your own CSV/XLSX/PDF/DOCX/TXT files, or **🗄 Connect PostgreSQL** with `postgresql://user:pass@db:5432/company_db` to use the database from step 4.

## Usage

### Fastest path: the demo dataset
1. Open the app and click **🚀 Try Demo**.
2. Ask a question right away, e.g.:
   * "How many employees are there?"
   * "Top five customers by revenue"
   * "Average salary by department"
   * "Highest selling product"
   * "Monthly revenue trend"

### Bring your own files
1. Click **📁 Upload Files** and drag in any mix of PDF, DOCX, TXT, CSV, or XLSX files.
2. Wait for processing to finish (a few seconds per file) — CSV/XLSX become SQL tables automatically, PDF/DOCX/TXT become searchable passages.
3. Ask questions like:
   * "Show top 10 customers" (from a CSV)
   * "Which department has the highest payroll?" (from an XLSX sheet)
   * "Summarize report.pdf"
   * "Compare employee counts with report findings" (hybrid: SQL + document search)
4. You can keep adding more files at any time from the same screen.

### Connect your own database
1. Click **🗄 Connect PostgreSQL** and enter a connection string.
2. Once connected, you can optionally add supporting documents (PDF/DOCX/TXT) alongside it — the database stays your primary SQL source, and hybrid queries pull from both.
3. Ask questions in plain English.

### Any mode
* The banner at the top always shows your **current datasource** and lets you switch (**Change data source**) back to the picker at any time.
* **Export** — download the current result set as CSV.
* **Query history** and **caching** work identically across all three modes.

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
| `POST` | `/api/datasource/postgres` | Connect to PostgreSQL, discover its schema, and activate it as the query engine's data source |
| `POST` | `/api/datasource/demo` | Activate the built-in offline demo dataset |
| `GET` | `/api/datasource/status` | Which data source (if any) is currently active, plus its schema |
| `POST` | `/api/datasource/reset` | Clear the active data source and any uploaded/indexed data |
| `POST` | `/api/upload-documents` | Upload a mixed batch of files (PDF/DOCX/TXT/CSV/XLSX) for background ingestion |
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
