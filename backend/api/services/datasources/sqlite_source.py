from typing import List, Dict

from sqlalchemy import create_engine, text

from ..schema_discovery import SchemaDiscovery
from .base import BaseSQLDataSource


class SQLiteDataSource(BaseSQLDataSource):
    """
    Base class for any SQL data source backed by a local SQLite file
    (uploaded spreadsheets, the demo dataset). Reuses the same generic
    SchemaDiscovery introspection used for PostgreSQL, so there is no
    duplicated schema-reading logic between data source types.
    """

    dialect = "sqlite"

    def __init__(self, db_path: str):
        self.db_path = db_path
        self.connection_string = f"sqlite:///{db_path}"
        self._engine = create_engine(
            self.connection_string, connect_args={"check_same_thread": False}
        )

    def get_schema(self) -> Dict:
        return SchemaDiscovery().analyze_database(self.connection_string)

    def execute(self, sql: str) -> List[Dict]:
        with self._engine.connect() as connection:
            result_proxy = connection.execute(text(sql))
            return [dict(row._mapping) for row in result_proxy]

    def describe(self) -> str:
        return "SQLite Database"
