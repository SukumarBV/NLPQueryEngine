# backend/api/services/query_engine.py (Final LLM Version)

import time
import os
import json
from sqlalchemy import create_engine, text
import google.generativeai as genai

from .schema_discovery import SchemaDiscovery

class QueryEngine:
    def __init__(self, connection_string: str):
        # Configure the Gemini API
        try:
            genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
            self.llm = genai.GenerativeModel('gemini-pro-latest')
        except Exception as e:
            raise Exception(f"Failed to configure Gemini AI. Check your API key. Error: {e}")
        
        # Discover schema and create DB engine
        self.schema = SchemaDiscovery().analyze_database(connection_string)
        self.db_engine = create_engine(connection_string, pool_size=10)
        print("Query Engine Initialized with LLM.")

    def process_query(self, user_query: str) -> dict:
        start_time = time.time()
        
        query_type = self._classify_query(user_query)
        results = None

        if query_type == "SQL":
            try:
                # Generate SQL using the LLM
                sql_query = self._generate_sql(user_query)
                self._validate_sql_query(sql_query) # Security check
                
                # Execute the generated SQL
                with self.db_engine.connect() as connection:
                    result_proxy = connection.execute(text(sql_query))
                    results = [dict(row._mapping) for row in result_proxy]
                    
            except Exception as e:
                return {"error": f"An error occurred: {e}"}

        else: # DOCUMENT or HYBRID
            results = f"{query_type} search is not fully implemented yet."

        return {
            "results": results,
            "query_type": query_type,
            "performance_metrics": {
                "response_time_seconds": round(time.time() - start_time, 2),
                "cache_hit": False
            },
            "generated_sql": sql_query if 'sql_query' in locals() else None
        }

    def _generate_sql(self, user_query: str) -> str:
        """Generates SQL from a user query using an LLM."""
        
        # Create a detailed prompt for the LLM
        prompt = f"""
        You are an expert Text-to-SQL model. Your task is to generate a single, executable SQL query for a PostgreSQL database.
        You must only output the SQL query and nothing else. Do not include any explanations or markdown formatting.

        Database Schema:
        {json.dumps(self.schema, indent=2)}

        User Question:
        "{user_query}"

        SQL Query:
        """
        
        print(f"--- Generating SQL for query: {user_query} ---")
        response = self.llm.generate_content(prompt)
        
        # Clean up the LLM's response to get only the SQL
        sql_query = response.text.strip()
        if sql_query.startswith("```sql"):
            sql_query = sql_query[6:]
        if sql_query.endswith("```"):
            sql_query = sql_query[:-3]
        
        print(f"--- Generated SQL: {sql_query} ---")
        return sql_query.strip()

    def _classify_query(self, user_query: str) -> str:
        # This can also be improved with an LLM call in the future
        doc_keywords = ["review", "skills", "resume", "performance"]
        is_doc = any(kw in user_query.lower() for kw in doc_keywords)
        if is_doc: return "HYBRID" # Assume most doc queries also need DB context
        return "SQL"

    def _validate_sql_query(self, sql: str):
        if not sql.strip().lower().startswith("select"):
            raise ValueError("LLM generated an invalid query. Only SELECT statements are allowed.")