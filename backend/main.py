from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import os
from dotenv import load_dotenv

from .api.routes import ingestion, query, schema
from .api.services.query_engine import QueryEngine

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
    """
    Application startup logic.
    We can pre-load models or initialize connections here.
    """
    # We will initialize the QueryEngine *after* a database is connected,
    # so we'll manage its state on the app object.
    app.state.query_engine = None
    print("FastAPI application started.")

# This is a new endpoint to initialize the query engine after DB connection
@app.post("/api/initialize-engine")
async def initialize_engine(payload: dict):
    """
    Initializes the query engine with a database connection string.
    This should be called by the frontend after a successful DB connection.
    """

    connection_string = payload.get("connection_string")
    if not connection_string:
        raise HTTPException(status_code=400, detail="Connection string is required.")
    
    try:
        # Create and store the engine instance on the app's state
        query_engine_instance = QueryEngine(connection_string=connection_string)
        app.state.query_engine = query_engine_instance
        
        # Also attach it to the routers so the dependency injection works
        query.router.query_engine_instance = query_engine_instance
        schema.router.query_engine_instance = query_engine_instance
        
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