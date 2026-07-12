from fastapi import APIRouter, UploadFile, HTTPException, BackgroundTasks, File
from typing import List, Dict
import os
import shutil
import tempfile
import uuid

from ..services.schema_discovery import SchemaDiscovery

router = APIRouter()
job_statuses: Dict[str, str] = {}

ALLOWED_EXTENSIONS = {".pdf", ".docx", ".txt"}
MAX_FILE_SIZE_BYTES = 20 * 1024 * 1024  # 20MB per file


@router.post("/connect-database")
async def connect_database(payload: Dict[str, str]):
    connection_string = payload.get("connection_string")
    if not connection_string:
        raise HTTPException(status_code=400, detail="Connection string is required.")
    try:
        discovery = SchemaDiscovery()
        schema = discovery.analyze_database(connection_string)
        return schema
    except ConnectionError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/upload-documents")
async def upload_documents(background_tasks: BackgroundTasks, files: List[UploadFile] = File(...)):
    if not files:
        raise HTTPException(status_code=400, detail="No files were provided.")

    document_processor = getattr(router, "document_processor", None)
    if document_processor is None:
        raise HTTPException(status_code=503, detail="Document processor is not ready yet.")

    job_id = str(uuid.uuid4())
    job_statuses[job_id] = "In Progress"

    upload_dir = os.path.join(tempfile.gettempdir(), f"nlp-query-engine-{job_id}")
    os.makedirs(upload_dir, exist_ok=True)

    file_paths = []
    try:
        for file in files:
            safe_name = os.path.basename(file.filename or "")
            extension = os.path.splitext(safe_name)[1].lower()
            if extension not in ALLOWED_EXTENSIONS:
                raise HTTPException(
                    status_code=400,
                    detail=f"Unsupported file type '{extension}'. Allowed types: PDF, DOCX, TXT.",
                )

            file_path = os.path.join(upload_dir, safe_name)
            size = 0
            with open(file_path, "wb") as buffer:
                while chunk := await file.read(1024 * 1024):
                    size += len(chunk)
                    if size > MAX_FILE_SIZE_BYTES:
                        raise HTTPException(
                            status_code=400, detail=f"File '{safe_name}' exceeds the 20MB limit."
                        )
                    buffer.write(chunk)
            file_paths.append(file_path)
    except HTTPException:
        shutil.rmtree(upload_dir, ignore_errors=True)
        raise
    except Exception as e:
        shutil.rmtree(upload_dir, ignore_errors=True)
        raise HTTPException(status_code=500, detail=f"Failed to save uploaded files: {e}")

    background_tasks.add_task(
        document_processor.process_documents, file_paths, job_id, job_statuses
    )

    return {"message": "Upload successful, processing started.", "job_id": job_id}


@router.get("/ingestion-status/{job_id}")
async def get_ingestion_status(job_id: str):
    status = job_statuses.get(job_id)
    if not status:
        raise HTTPException(status_code=404, detail="Job ID not found.")
    return {"job_id": job_id, "status": status}
