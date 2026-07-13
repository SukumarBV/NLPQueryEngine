from fastapi import APIRouter, HTTPException
from typing import Dict

from ..services.engine_manager import get_engine_manager

router = APIRouter()


@router.post("/postgres")
async def connect_postgres(payload: Dict[str, str]):
    """Connects to a user-supplied PostgreSQL database and activates it as the query engine's data source."""
    connection_string = payload.get("connection_string")
    if not connection_string:
        raise HTTPException(status_code=400, detail="Connection string is required.")

    manager = get_engine_manager()
    try:
        schema = manager.connect_postgres(connection_string)
    except ConnectionError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to connect: {e}")

    return {"message": "Connected to PostgreSQL.", **manager.status()}


@router.post("/demo")
async def use_demo():
    """Activates the built-in offline demo dataset."""
    manager = get_engine_manager()
    try:
        manager.use_demo()
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load demo dataset: {e}")

    return {"message": "Demo dataset ready.", **manager.status()}


@router.get("/status")
async def status():
    """Returns which data source (if any) is currently active."""
    manager = get_engine_manager()
    return manager.status()


@router.post("/reset")
async def reset():
    """Clears the active data source and any uploaded/indexed data."""
    manager = get_engine_manager()
    manager.reset()
    return {"message": "Data source reset."}
