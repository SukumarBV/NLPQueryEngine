# backend/api/routes/ingestion.py (Updated)
from fastapi import APIRouter, UploadFile, HTTPException, BackgroundTasks, File
from typing import List, Dict
import shutil
import os
import uuid

from ..services.schema_discovery import SchemaDiscovery

router = APIRouter()
job_statuses: Dict[str, str] = {}

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
            
    # Use the shared document_processor instance from the router
    background_tasks.add_task(router.document_processor.process_documents, file_paths, job_id, job_statuses)
    
    return {"message": "Upload successful, processing started.", "job_id": job_id}

@router.get("/ingestion-status/{job_id}")
async def get_ingestion_status(job_id: str):
    status = job_statuses.get(job_id)
    if not status:
        raise HTTPException(status_code=404, detail="Job ID not found.")
    return {"job_id": job_id, "status": status}
