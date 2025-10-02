from fastapi import APIRouter, UploadFile, HTTPException, BackgroundTasks, File
from typing import List, Dict
import shutil
import os
import uuid

from ..services.schema_discovery import SchemaDiscovery
from ..services.document_processor import DocumentProcessor

router = APIRouter()
document_processor = DocumentProcessor()

# In-memory storage for job statuses (replace with Redis/Celery in production)
job_statuses: Dict[str, str] = {}

@router.post("/connect-database")
async def connect_database(payload: Dict[str, str]):
    """
    Connects to the database and discovers its schema.
    """
    connection_string = payload.get("connection_string")
    if not connection_string:
        raise HTTPException(status_code=400, detail="Connection string is required.")
    
    try:
        discovery = SchemaDiscovery()
        schema = discovery.analyze_database(connection_string)
        # In a real app, this schema would be stored in a shared state
        # or database for the QueryEngine to use.
        return schema
    except ConnectionError as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/upload-documents")
async def upload_documents(background_tasks: BackgroundTasks, files: List[UploadFile] = File(...)):
    """
    Accepts multiple document uploads and processes them in the background.
    """
    job_id = str(uuid.uuid4())
    job_statuses[job_id] = "In Progress"
    
    upload_dir = f"/tmp/{job_id}"
    os.makedirs(upload_dir, exist_ok=True)
    
    file_paths = []
    for file in files:
        file_path = os.path.join(upload_dir, file.filename)
        file_paths.append(file_path)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
    # Add document processing to the background
    background_tasks.add_task(document_processor.process_documents, file_paths, job_id)
    
    return {"message": "Upload successful, processing started.", "job_id": job_id}

@router.get("/ingestion-status/{job_id}")
async def get_ingestion_status(job_id: str):
    """
    Returns the progress of document processing.
    """
    status = job_statuses.get(job_id)
    if not status:
        raise HTTPException(status_code=404, detail="Job ID not found.")
    
    # Simple status check. In a real app, this would be more detailed.
    # For instance, you could check if the background task is done.
    return {"job_id": job_id, "status": status}