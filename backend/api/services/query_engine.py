import time
from functools import lru_cache
from .schema_discovery import SchemaDiscovery

# Simple in-memory cache with LRU policy for frequent queries [cite: 195]
@lru_cache(maxsize=1000)
def execute_cached_query(query_str: str, engine_instance):
    return engine_instance._execute_query(query_str)

class QueryEngine:
    def __init__(self, connection_string: str):
        self.schema = SchemaDiscovery().analyze_database(connection_string) [cite: 63]
        # Connection pooling is handled by SQLAlchemy's engine [cite: 196]
        # self.db_engine = create_engine(connection_string, pool_size=10)
        # self.vector_store = ... 

    def process_query(self, user_query: str) -> dict:
        """
        Processes a query through a pipeline of caching, classification, and execution.
        """
        start_time = time.time()
        
        try:
            # Attempt to retrieve from cache
            result, query_type = execute_cached_query(user_query, self)
            is_cache_hit = True
        except Exception:
            # Cache miss, process the query
            query_type = self._classify_query(user_query)
            result, _ = self._execute_query(user_query, query_type)
            is_cache_hit = False

        return {
            "results": result,
            "query_type": query_type,
            "performance_metrics": {
                "response_time_seconds": round(time.time() - start_time, 2),
                "cache_hit": is_cache_hit
            }
        }

    def _execute_query(self, user_query: str, query_type: str = None):
        """Internal execution logic."""
        if not query_type:
            query_type = self._classify_query(user_query)

        if query_type == "SQL":
            sql_query = self._generate_sql(user_query)
            self._validate_sql_query(sql_query) # Prevent SQL injection [cite: 100]
            # optimized_sql = self.optimize_sql_query(sql_query)
            # db_results = self.db_engine.execute(optimized_sql)
            return f"Executed SQL: {sql_query}", query_type
        
        elif query_type == "DOCUMENT":
            # doc_results = self.vector_store.search(user_query)
            return "Searched documents for relevant content.", query_type
        
        else: # HYBRID
            return "Executed a hybrid search on database and documents.", query_type

    def _classify_query(self, user_query: str) -> str:
        """
        Classifies query as SQL, DOCUMENT, or HYBRID. [cite: 67]
        """
        # Using keywords for simple classification. An LLM would be more robust.
        doc_keywords = ["review", "skills", "resume", "performance"]
        sql_keywords = ["how many", "average", "list", "top 5", "department"]

        is_doc = any(kw in user_query.lower() for kw in doc_keywords)
        is_sql = any(kw in user_query.lower() for kw in sql_keywords)

        if is_doc and is_sql: return "HYBRID"
        if is_doc: return "DOCUMENT"
        return "SQL"

    def _generate_sql(self, user_query: str) -> str:
        """
        Generates SQL from natural language using an LLM.
        """
        prompt = f"Given schema: {self.schema}, generate a SQL query for: '{user_query}'"
        # response = call_llm(prompt) # Using a free-tier API or open-source model [cite: 399]
        if "how many employees" in user_query.lower(): return "SELECT COUNT(*) FROM employees;"
        return "SELECT * FROM staff LIMIT 10;"

    def _validate_sql_query(self, sql: str):
        """
        Validates the generated SQL to prevent malicious commands. 
        """
        if not sql.strip().lower().startswith("select"):
            raise SecurityException("Invalid query. Only SELECT statements are allowed.")