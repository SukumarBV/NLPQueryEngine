from typing import List, Dict

from sqlalchemy import create_engine, text

from ..schema_discovery import SchemaDiscovery
from .base import BaseSQLDataSource


class PostgresDataSource(BaseSQLDataSource):
    """Wraps a user-supplied PostgreSQL connection string."""

    dialect = "postgresql"

    def __init__(self, connection_string: str):
        self.connection_string = connection_string
        # analyze_database validates the connection and raises ConnectionError
        # with a friendly message if it's unreachable/invalid.
        self._schema = SchemaDiscovery().analyze_database(connection_string)
        self._engine = create_engine(
            connection_string, pool_size=5, max_overflow=2, pool_pre_ping=True
        )

    def get_schema(self) -> Dict:
        return self._schema

    def execute(self, sql: str) -> List[Dict]:
        with self._engine.connect() as connection:
            result_proxy = connection.execute(text(sql))
            return [dict(row._mapping) for row in result_proxy]

    def describe(self) -> str:
        return "PostgreSQL Database"
