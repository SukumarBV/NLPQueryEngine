import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from api.routes import ingestion, query, schema
from api.services.document_processor import DocumentProcessor
from api.services.query_engine import QueryEngine

load_dotenv()

# Directory containing the built React frontend (created by the Docker
# build). When absent (e.g. running the backend alone during local
# development), the API still works; only static serving is skipped.
STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create a single, shared instance of the document processor.
    app.state.document_processor = DocumentProcessor()
    ingestion.router.document_processor = app.state.document_processor
    app.state.query_engine = None
    print("FastAPI application started.")
    yield


app = FastAPI(title="NLP Query Engine API", lifespan=lifespan)

allowed_origins_env = os.getenv("ALLOWED_ORIGINS", "*")
allowed_origins = (
    ["*"] if allowed_origins_env.strip() == "*" else [o.strip() for o in allowed_origins_env.split(",") if o.strip()]
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=allowed_origins != ["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/api/initialize-engine")
async def initialize_engine(payload: dict):
    connection_string = payload.get("connection_string")
    if not connection_string:
        raise HTTPException(status_code=400, detail="Connection string is required.")

    try:
        query_engine_instance = QueryEngine(
            connection_string=connection_string,
            document_processor=app.state.document_processor,
        )
        app.state.query_engine = query_engine_instance

        query.router.query_engine_instance = query_engine_instance
        schema.router.query_engine_instance = query_engine_instance

        print("Query engine initialized successfully.")
        return {"message": "Query engine initialized successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to initialize query engine: {e}")


app.include_router(ingestion.router, prefix="/api", tags=["Ingestion"])
app.include_router(query.router, prefix="/api", tags=["Query"])
app.include_router(schema.router, prefix="/api", tags=["Schema"])


@app.get("/api/health")
def health_check():
    return {"status": "NLP Query Engine API is running."}


# Serve the built React frontend, if present, so the whole app can run as
# a single deployable service (this is what the root Dockerfile builds).
if os.path.isdir(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=os.path.join(STATIC_DIR, "static")), name="static-assets")

    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        if full_path.startswith("api/"):
            raise HTTPException(status_code=404, detail="Not found.")
        candidate = os.path.join(STATIC_DIR, full_path)
        if full_path and os.path.isfile(candidate):
            return FileResponse(candidate)
        return FileResponse(os.path.join(STATIC_DIR, "index.html"))
else:
    @app.get("/")
    def read_root():
        return {"status": "NLP Query Engine API is running. (No frontend build found.)"}
