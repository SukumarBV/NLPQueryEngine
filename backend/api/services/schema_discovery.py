from sqlalchemy import create_engine, inspect

class SchemaDiscovery:
    """
    Dynamically discovers the schema of a SQL database.
    """
    def analyze_database(self, connection_string: str) -> dict:
        """
        Connects to a database to discover tables, columns, and relationships. [cite: 43]
        """
        try:
            engine = create_engine(connection_string)
            inspector = inspect(engine)
            schema_info = {"tables": []}
            
            for table_name in inspector.get_table_names():
                columns = [
                    {"name": col['name'], "type": str(col['type'])}
                    for col in inspector.get_columns(table_name)
                ]
                foreign_keys = inspector.get_foreign_keys(table_name)
                
                schema_info["tables"].append({
                    "name": table_name,
                    "columns": columns,
                    "foreign_keys": foreign_keys
                })
            return schema_info
        except Exception as e:
     
            raise ConnectionError(f"Database connection failed: {e}")

    def map_natural_language_to_schema(self, query: str, schema: dict) -> dict:
        """
        Maps natural language terms to schema elements.
        Example: "salary" -> "compensation" [cite: 55]
        """
        term_map = {}
        for term in ["salary", "pay", "compensation"]:
            if term in query.lower():
                for table in schema.get("tables", []):
                    for col in table.get("columns", []):
                        if any(c in col["name"] for c in ["salary", "compensation", "pay"]):
                            term_map[term] = f"{table['name']}.{col['name']}"
        return term_map
