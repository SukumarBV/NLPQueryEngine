import os
import shutil
from pathlib import Path
from typing import Dict, List, Optional

from .datasources.demo_source import DemoDataSource
from .datasources.postgres_source import PostgresDataSource
from .datasources.upload_source import SQLiteUploadDataSource
from .document_processor import DocumentProcessor
from .query_engine import QueryEngine

DOCUMENT_EXTENSIONS = {".pdf", ".docx", ".txt"}
STRUCTURED_EXTENSIONS = {".csv", ".xlsx", ".xls"}
ALLOWED_EXTENSIONS = DOCUMENT_EXTENSIONS | STRUCTURED_EXTENSIONS


class EngineManager:
    """
    Owns the single active QueryEngine for this server instance and the
    shared document store, and knows how to (re)build the engine for
    each of the three data-source modes: postgres, uploads, demo.

    This app is a single-tenant demo tool (one active session per running
    instance, matching its existing in-memory design), so a process-wide
    singleton keeps the routers simple instead of threading a datasource
    choice through request state.
    """

    def __init__(self):
        self.document_processor = DocumentProcessor()
        self.upload_datasource = SQLiteUploadDataSource()
        self.engine: Optional[QueryEngine] = None
        self.mode: Optional[str] = None  # "postgres" | "uploads" | "demo"

    # ---- activation ----

    def connect_postgres(self, connection_string: str) -> dict:
        datasource = PostgresDataSource(connection_string)
        self.engine = QueryEngine(datasource, self.document_processor)
        self.mode = "postgres"
        return self.engine.schema

    def use_demo(self) -> dict:
        datasource = DemoDataSource()
        self.engine = QueryEngine(datasource, self.document_processor)
        self.mode = "demo"
        return self.engine.schema

    def activate_uploads(self) -> dict:
        self.engine = QueryEngine(self.upload_datasource, self.document_processor)
        self.mode = "uploads"
        return self.engine.schema

    def reset(self):
        """Clears all active state so the user can pick a data source again."""
        self.upload_datasource.reset()
        self.document_processor.vector_store.clear()
        self.engine = None
        self.mode = None

    # ---- status ----

    def status(self) -> dict:
        return {
            "mode": self.mode,
            "label": self.engine.datasource.describe() if self.engine else None,
            "schema": self.engine.schema if self.engine else None,
            "document_count": len(self.document_processor.vector_store),
        }

    # ---- uploads ----

    def process_uploaded_batch(self, file_paths: List[str], job_id: str, job_statuses: Dict):
        job_statuses[job_id] = "In Progress"

        doc_paths = [p for p in file_paths if Path(p).suffix.lower() in DOCUMENT_EXTENSIONS]
        structured_paths = [p for p in file_paths if Path(p).suffix.lower() in STRUCTURED_EXTENSIONS]

        errors: List[str] = []

        for path in structured_paths:
            try:
                self.upload_datasource.load_file(path)
            except Exception as e:
                errors.append(f"{os.path.basename(path)}: {e}")

        if doc_paths:
            # process_documents reports its own per-file failures into this
            # temporary dict instead of the batch's job_statuses entry, so a
            # single bad document doesn't overwrite structured-file results.
            doc_job_statuses: Dict[str, str] = {}
            self.document_processor.process_documents(doc_paths, job_id, doc_job_statuses)
            doc_result = doc_job_statuses.get(job_id, "Complete")
            if isinstance(doc_result, str) and doc_result.startswith("Failed"):
                errors.append(doc_result)

        # Clean up the shared upload directory now that both structured and
        # document files (if any) have been read.
        if file_paths:
            shutil.rmtree(os.path.dirname(file_paths[0]), ignore_errors=True)

        # If new structured tables were added, they become (or stay) the
        # active SQL data source. But if the user is uploading a document
        # on top of an already-connected PostgreSQL or demo database, keep
        # that data source active rather than silently switching to the
        # (empty) uploads data source — the shared document store the
        # existing engine already points at picks up the new document
        # automatically, no reactivation needed.
        should_activate_uploads = bool(structured_paths) or self.mode in (None, "uploads")
        if should_activate_uploads:
            try:
                self.activate_uploads()
            except Exception as e:
                errors.append(f"Could not activate uploaded data: {e}")

        job_statuses[job_id] = ("Failed: " + "; ".join(errors)) if errors else "Complete"


# Process-wide singleton. Created explicitly during FastAPI's startup
# (after environment variables are loaded) rather than at import time,
# so GEMINI_API_KEY is guaranteed to be available before the
# DocumentProcessor tries to read it.
_manager: Optional["EngineManager"] = None


def init_engine_manager() -> "EngineManager":
    global _manager
    _manager = EngineManager()
    return _manager


def get_engine_manager() -> "EngineManager":
    if _manager is None:
        raise RuntimeError("EngineManager has not been initialized yet.")
    return _manager
