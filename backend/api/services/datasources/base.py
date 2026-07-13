from abc import ABC, abstractmethod
from typing import List, Dict


class BaseSQLDataSource(ABC):
    """
    Common interface every queryable SQL backend implements, so the
    QueryEngine and its LLM-driven SQL generation never need to know
    whether they're talking to PostgreSQL, an uploaded spreadsheet, or
    the built-in demo database.
    """

    #: SQL dialect hint passed to the LLM prompt (e.g. "postgresql", "sqlite").
    dialect: str = "sql"

    @abstractmethod
    def get_schema(self) -> Dict:
        """Return {"tables": [{"name", "columns": [...], "foreign_keys": [...]}]}"""
        raise NotImplementedError

    @abstractmethod
    def execute(self, sql: str) -> List[Dict]:
        """Execute a read-only SQL query and return rows as a list of dicts."""
        raise NotImplementedError

    def describe(self) -> str:
        """Human-readable label shown in the UI (e.g. "Demo Database")."""
        return "SQL Data Source"
