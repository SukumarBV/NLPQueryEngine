from fastapi import APIRouter, HTTPException

from ..services.engine_manager import get_engine_manager

router = APIRouter()


@router.get("/schema")
async def get_schema():
    """Returns the current discovered schema for visualization."""
    manager = get_engine_manager()
    if manager.engine is None or not manager.engine.schema:
        raise HTTPException(
            status_code=404,
            detail="No schema available yet. Connect a database, upload files, or use the demo dataset first.",
        )
    return manager.engine.schema
