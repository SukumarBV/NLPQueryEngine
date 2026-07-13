from fastapi import APIRouter, HTTPException
from typing import Dict

from ..services.engine_manager import get_engine_manager

router = APIRouter()


@router.post("/query")
async def process_query(payload: Dict[str, str]):
    """
    Processes a natural language query against whichever data source is
    currently active (PostgreSQL, uploaded files, or the demo dataset).
    """
    user_query = (payload.get("query") or "").strip()
    if not user_query:
        raise HTTPException(status_code=400, detail="Query cannot be empty.")

    manager = get_engine_manager()
    if manager.engine is None:
        raise HTTPException(
            status_code=503,
            detail="No data source is active yet. Connect a database, upload files, or use the demo dataset first.",
        )

    try:
        return manager.engine.process_query(user_query)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {e}")


@router.get("/query/history")
async def get_query_history():
    """Returns the most recent queries processed by the engine, most recent first."""
    manager = get_engine_manager()
    if manager.engine is None:
        return {"history": []}
    return {"history": manager.engine.get_history()}
