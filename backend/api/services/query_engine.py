import os
import re
import time
from collections import OrderedDict
from typing import Optional

import numpy as np
from sqlalchemy import create_engine, text
from google import genai

from .document_processor import DocumentProcessor
from .schema_discovery import SchemaDiscovery

GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

# Keywords that should never appear in a generated query. This is a
# defense-in-depth guard on top of only ever executing the query as a
# read-only statement; it is not a substitute for using a database
# role that only has SELECT privileges.
FORBIDDEN_SQL_KEYWORDS = {
    "insert", "update", "delete", "drop", "alter", "truncate",
    "create", "grant", "revoke", "attach", "detach", "replace",
    "exec", "execute", "call", "merge", "vacuum", "copy",
}

DOC_KEYWORDS = [
    "review", "resume", "cv", "skills", "performance", "project",
    "document", "report", "feedback", "policy", "contract", "note",
]

MAX_HISTORY = 50
MAX_CACHE_ENTRIES = 200


class QueryEngine:
    def __init__(self, connection_string: str, document_processor: DocumentProcessor):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError(
                "GEMINI_API_KEY is not set. Add it to the server's environment variables."
            )
        self.client = genai.Client(api_key=api_key)
        self.document_processor = document_processor

        self.schema = SchemaDiscovery().analyze_database(connection_string)
        self.db_engine = create_engine(
            connection_string, pool_size=5, max_overflow=2, pool_pre_ping=True
        )

        self._cache: "OrderedDict[str, dict]" = OrderedDict()
        self._history: list = []
        print("Query Engine initialized with LLM and Document Processor.")

    def process_query(self, user_query: str) -> dict:
        start_time = time.time()
        cache_key = user_query.strip().lower()

        if cache_key in self._cache:
            cached = self._cache[cache_key]
            result = dict(cached)
            result["performance_metrics"] = {
                "response_time_seconds": round(time.time() - start_time, 4),
                "cache_hit": True,
            }
            self._record_history(user_query, result["query_type"])
            return result

        query_type = self._classify_query(user_query)
        sql_query: Optional[str] = None
        sql_results = None
        doc_results = None

        try:
            if query_type in ("SQL", "HYBRID") and self.schema.get("tables"):
                sql_query = self._generate_sql(user_query)
                self._validate_sql_query(sql_query)
                with self.db_engine.connect() as connection:
                    result_proxy = connection.execute(text(sql_query))
                    sql_results = [dict(row._mapping) for row in result_proxy]

            if query_type in ("DOCUMENT", "HYBRID"):
                doc_results = self._search_documents(user_query)
        except Exception as e:
            return {
                "error": str(e),
                "query_type": query_type,
                "generated_sql": sql_query,
            }

        if query_type == "HYBRID":
            results = {"database": sql_results or [], "documents": doc_results or []}
        elif query_type == "SQL":
            results = sql_results or []
        else:
            results = doc_results or []

        response = {
            "results": results,
            "query_type": query_type,
            "performance_metrics": {
                "response_time_seconds": round(time.time() - start_time, 2),
                "cache_hit": False,
            },
            "generated_sql": sql_query,
        }

        self._cache[cache_key] = response
        if len(self._cache) > MAX_CACHE_ENTRIES:
            self._cache.popitem(last=False)
        self._record_history(user_query, query_type)

        return response

    def _record_history(self, user_query: str, query_type: str):
        self._history.append({"query": user_query, "query_type": query_type})
        if len(self._history) > MAX_HISTORY:
            self._history.pop(0)

    def get_history(self) -> list:
        return list(reversed(self._history[-20:]))

    def _search_documents(self, user_query: str, top_k: int = 3) -> list:
        """Performs a vector search on the ingested documents."""
        store = self.document_processor.vector_store
        if not store:
            return []

        query_embedding = self.document_processor.embed_query(user_query)

        doc_ids = list(store.keys())
        doc_embeddings = np.array([store[doc_id]["embedding"] for doc_id in doc_ids])

        query_norm = query_embedding / (np.linalg.norm(query_embedding) + 1e-10)
        doc_norms = doc_embeddings / (
            np.linalg.norm(doc_embeddings, axis=1, keepdims=True) + 1e-10
        )

        similarities = np.dot(doc_norms, query_norm)

        k = min(top_k, len(doc_ids))
        top_k_indices = np.argsort(similarities)[-k:][::-1]

        results = []
        for index in top_k_indices:
            doc_id = doc_ids[index]
            results.append(
                {
                    "content": store[doc_id]["content"],
                    "source": store[doc_id]["source"],
                    "similarity": float(similarities[index]),
                }
            )
        return results

    def _generate_sql(self, user_query: str) -> str:
        import json

        prompt = f"""You are an expert Text-to-SQL model. Your task is to generate a single, executable, read-only SQL query for a PostgreSQL database.
You must only output the SQL query and nothing else. Do not include any explanations or markdown formatting.
Only ever generate a single SELECT statement. Never generate INSERT, UPDATE, DELETE, DROP, ALTER, or any other statement that modifies data or schema.

Database Schema:
{json.dumps(self.schema, indent=2)}

User Question:
"{user_query}"

SQL Query:
"""
        response = self.client.models.generate_content(model=GEMINI_MODEL, contents=prompt)
        sql_query = (response.text or "").strip()
        sql_query = re.sub(r"^```(sql)?", "", sql_query, flags=re.IGNORECASE).strip()
        sql_query = re.sub(r"```$", "", sql_query).strip()
        return sql_query

    def _classify_query(self, user_query: str) -> str:
        query_lower = user_query.lower()
        has_doc_keyword = any(kw in query_lower for kw in DOC_KEYWORDS)
        has_tables = bool(self.schema.get("tables"))
        has_documents = bool(self.document_processor.vector_store)

        if has_doc_keyword and has_tables:
            return "HYBRID"
        if has_doc_keyword or (not has_tables and has_documents):
            return "DOCUMENT"
        return "SQL"

    def _validate_sql_query(self, sql: str):
        cleaned = sql.strip().rstrip(";").strip()
        if not cleaned:
            raise ValueError("The model did not return a SQL query.")

        lowered = cleaned.lower()
        if not lowered.startswith("select"):
            raise ValueError("Generated an invalid query. Only SELECT statements are allowed.")
        if ";" in cleaned:
            raise ValueError("Multiple SQL statements are not allowed.")
        for keyword in FORBIDDEN_SQL_KEYWORDS:
            if re.search(rf"\b{keyword}\b", lowered):
                raise ValueError(f"Query contains a forbidden keyword: {keyword}")
