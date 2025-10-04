# backend/main.py (Updated)
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from api.routes import ingestion, query, schema
from api.services.query_engine import QueryEngine
from api.services.document_processor import DocumentProcessor

load_dotenv()

app = FastAPI(title="NLP Query Engine API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup_event():
    # Create a single, shared instance of the document processor
    app.state.document_processor = DocumentProcessor()
    # Pass this instance to the ingestion router
    ingestion.router.document_processor = app.state.document_processor
    app.state.query_engine = None
    print("FastAPI application started.")

@app.post("/api/initialize-engine")
async def initialize_engine(payload: dict):
    connection_string = payload.get("connection_string")
    if not connection_string:
        raise HTTPException(status_code=400, detail="Connection string is required.")
    
    try:
        # Pass the shared document processor to the query engine
        query_engine_instance = QueryEngine(
            connection_string=connection_string,
            document_processor=app.state.document_processor
        )
        app.state.query_engine = query_engine_instance
        
        query.router.query_engine_instance = query_engine_instance
        schema.router.query_engine_instance = query_engine_instance
        
        print("Query engine initialized successfully.")
        return {"message": "Query engine initialized successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to initialize query engine: {e}")

app.include_router(ingestion.router, prefix="/api", tags=["Ingestion"])
app.include_router(query.router, prefix="/api", tags=["Query"])
app.include_router(schema.router, prefix="/api", tags=["Schema"])

@app.get("/")
def read_root():
    return {"status": "NLP Query Engine API is running."}