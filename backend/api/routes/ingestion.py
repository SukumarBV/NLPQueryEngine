from fastapi import APIRouter, UploadFile, HTTPException, BackgroundTasks, File
from typing import List, Dict
import os
import shutil
import tempfile
import uuid

from ..services.engine_manager import ALLOWED_EXTENSIONS, get_engine_manager

router = APIRouter()
job_statuses: Dict[str, str] = {}

MAX_FILE_SIZE_BYTES = 20 * 1024 * 1024  # 20MB per file


@router.post("/upload-documents")
async def upload_documents(background_tasks: BackgroundTasks, files: List[UploadFile] = File(...)):
    """
    Accepts a mixed batch of files. PDF/DOCX/TXT are chunked and embedded
    for semantic search; CSV/XLSX are loaded into queryable SQL tables.
    Once processing finishes, the uploaded data is activated automatically
    so it can be queried right away.
    """
    if not files:
        raise HTTPException(status_code=400, detail="No files were provided.")

    manager = get_engine_manager()

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
                    detail=(
                        f"Unsupported file type '{extension}'. "
                        "Allowed types: PDF, DOCX, TXT, CSV, XLSX."
                    ),
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

    background_tasks.add_task(manager.process_uploaded_batch, file_paths, job_id, job_statuses)

    return {"message": "Upload successful, processing started.", "job_id": job_id}


@router.get("/ingestion-status/{job_id}")
async def get_ingestion_status(job_id: str):
    status = job_statuses.get(job_id)
    if not status:
        raise HTTPException(status_code=404, detail="Job ID not found.")
    return {"job_id": job_id, "status": status}
