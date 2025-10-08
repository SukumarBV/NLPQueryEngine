from fastapi import APIRouter, Depends, HTTPException
from ..services.query_engine import QueryEngine

router = APIRouter()

def get_query_engine_from_app():

    if not hasattr(router, "query_engine_instance"):
        raise HTTPException(status_code=503, detail="Schema not available. Connect to a database first.")
    return router.query_engine_instance

@router.get("/schema")
async def get_schema(engine: QueryEngine = Depends(get_query_engine_from_app)):
    """
    Returns the current discovered schema for visualization.
    """
    if not engine.schema or "error" in engine.schema:
        raise HTTPException(status_code=404, detail="Schema not found or failed to load.")
    return engine.schema
