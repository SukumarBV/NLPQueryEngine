# backend/main.py (Fully Corrected Version)

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import os
from dotenv import load_dotenv

# These imports are now fixed (no dots at the beginning)
from api.routes import ingestion, query, schema
from api.services.query_engine import QueryEngine

# Load environment variables from .env file
load_dotenv()

app = FastAPI(
    title="NLP Query Engine API",
    description="API for querying structured and unstructured employee data.",
    version="1.0.0"
)

# Configure CORS to allow frontend requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"], # Adjust for your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup_event():
    app.state.query_engine = None
    print("FastAPI application started. Waiting for database connection...")

@app.post("/api/initialize-engine")
async def initialize_engine(payload: dict):
    connection_string = payload.get("connection_string")
    if not connection_string:
        raise HTTPException(status_code=400, detail="Connection string is required.")
    
    try:
        query_engine_instance = QueryEngine(connection_string=connection_string)
        app.state.query_engine = query_engine_instance
        
        query.router.query_engine_instance = query_engine_instance
        schema.router.query_engine_instance = query_engine_instance
        
        print("Query engine initialized successfully.")
        return {"message": "Query engine initialized successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to initialize query engine: {e}")

# Include the API routers
app.include_router(ingestion.router, prefix="/api", tags=["Ingestion"])
app.include_router(query.router, prefix="/api", tags=["Query"])
app.include_router(schema.router, prefix="/api", tags=["Schema"])

@app.get("/")
def read_root():
    return {"status": "NLP Query Engine API is running."}