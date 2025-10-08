# backend/api/services/query_engine.py (Updated)
import time
import os
import json
from sqlalchemy import create_engine, text
import google.generativeai as genai
import numpy as np

from .schema_discovery import SchemaDiscovery
from .document_processor import DocumentProcessor

class QueryEngine:
    def __init__(self, connection_string: str, document_processor: DocumentProcessor):
        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
        self.llm = genai.GenerativeModel('gemini-pro-latest')
        
        self.document_processor = document_processor
        
        self.schema = SchemaDiscovery().analyze_database(connection_string)
        self.db_engine = create_engine(connection_string, pool_size=10)
        print("Query Engine Initialized with LLM and Document Processor.")

    def process_query(self, user_query: str) -> dict:
        start_time = time.time()
        query_type = self._classify_query(user_query)
        results = None
        sql_query = None

        try:
            if query_type == "SQL":
                sql_query = self._generate_sql(user_query)
                self._validate_sql_query(sql_query)
                with self.db_engine.connect() as connection:
                    result_proxy = connection.execute(text(sql_query))
                    results = [dict(row._mapping) for row in result_proxy]
            
            # --- NEW DOCUMENT SEARCH LOGIC ---
            elif query_type in ["DOCUMENT", "HYBRID"]:
                # For hybrid, we could optionally run a SQL query first.
                # For simplicity, we will just search the documents.
                results = self._search_documents(user_query)

        except Exception as e:
            return {"error": f"An error occurred: {e}"}

        return {
            "results": results,
            "query_type": query_type,
            "performance_metrics": { "response_time_seconds": round(time.time() - start_time, 2), "cache_hit": False },
            "generated_sql": sql_query
        }

    def _search_documents(self, user_query: str, top_k=3) -> list:
        """Performs a vector search on the documents."""
        if not self.document_processor.vector_store:
            return []
        
        # 1. Create an embedding for the user's query
        query_embedding = self.document_processor.embedding_model.encode(user_query)
        
        # 2. Get all document embeddings from the vector store
        doc_ids = list(self.document_processor.vector_store.keys())
        doc_embeddings = np.array([self.document_processor.vector_store[id]['embedding'] for id in doc_ids])
        
        # 3. Calculate cosine similarity
        # Normalize embeddings to unit vectors
        query_embedding_norm = query_embedding / np.linalg.norm(query_embedding)
        doc_embeddings_norm = doc_embeddings / np.linalg.norm(doc_embeddings, axis=1, keepdims=True)
        
        # Compute dot product (cosine similarity for normalized vectors)
        similarities = np.dot(doc_embeddings_norm, query_embedding_norm)
        
        # 4. Get the top_k results
        top_k_indices = np.argsort(similarities)[-top_k:][::-1]
        
        # 5. Format and return the results
        results = []
        for index in top_k_indices:
            doc_id = doc_ids[index]
            results.append({
                "content": self.document_processor.vector_store[doc_id]['content'],
                "source": self.document_processor.vector_store[doc_id]['source'],
                "similarity": float(similarities[index])
            })
        return results

   
    def _generate_sql(self, user_query: str) -> str:
        prompt = f"""
        You are an expert Text-to-SQL model. Your task is to generate a single, executable SQL query for a PostgreSQL database.
        You must only output the SQL query and nothing else. Do not include any explanations or markdown formatting.

        Database Schema:
        {json.dumps(self.schema, indent=2)}

        User Question:
        "{user_query}"

        SQL Query:
        """
        response = self.llm.generate_content(prompt)
        sql_query = response.text.strip()
        if sql_query.startswith("```sql"): sql_query = sql_query[6:]
        if sql_query.endswith("```"): sql_query = sql_query[:-3]
        return sql_query.strip()

    def _classify_query(self, user_query: str) -> str:
        doc_keywords = ["review", "skills", "resume", "performance", "project"]
        is_doc = any(kw in user_query.lower() for kw in doc_keywords)
        if is_doc: return "HYBRID"
        return "SQL"

    def _validate_sql_query(self, sql: str):
        if not sql.strip().lower().startswith("select"):
            raise ValueError("LLM generated an invalid query. Only SELECT statements are allowed.")
