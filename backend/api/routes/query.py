from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, List

from ..services.query_engine import QueryEngine

router = APIRouter()

# This is a placeholder for a shared QueryEngine instance.
# In main.py, we will manage its lifecycle.
def get_query_engine():
    # This dependency injection would be more robust in the main app setup
    # to handle the connection string properly.
    # For now, we assume it's initialized elsewhere.
    if not hasattr(router, "query_engine_instance"):
        raise HTTPException(status_code=503, detail="Query Engine not initialized. Connect to a database first.")
    return router.query_engine_instance

@router.post("/query")
async def process_query(payload: Dict[str, str], engine: QueryEngine = Depends(get_query_engine)):
    """
    Processes a natural language query.
    Returns results, query type, performance metrics, and sources.
    """
    user_query = payload.get("query")
    if not user_query:
        raise HTTPException(status_code=400, detail="Query cannot be empty.")
    
    try:
        result = engine.process_query(user_query)
        return result
    except Exception as e:
        # Handle errors gracefully
        raise HTTPException(status_code=500, detail=f"An error occurred: {e}")

@router.get("/query/history")
async def get_query_history():
    """

    Gets previous queries to demonstrate caching.
    This is a simplified implementation.
    """
    # lru_cache doesn't expose its keys easily, so we'll simulate.
    # In a real app, you'd have a separate history log.
    return {"history": ["This is a demo endpoint for query history."]}