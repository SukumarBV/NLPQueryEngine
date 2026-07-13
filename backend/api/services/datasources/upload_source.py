import os
import re
import tempfile
import uuid
from pathlib import Path

import pandas as pd

from .sqlite_source import SQLiteDataSource


class SQLiteUploadDataSource(SQLiteDataSource):
    """
    Accumulates uploaded CSV/XLSX files into queryable SQL tables backed
    by a private SQLite file. Each CSV becomes one table; each worksheet
    in an XLSX workbook becomes its own table (sheet names are preserved
    as closely as SQL identifiers allow).
    """

    def __init__(self):
        db_path = os.path.join(tempfile.gettempdir(), f"nlp-query-engine-uploads-{uuid.uuid4().hex}.db")
        super().__init__(db_path)
        self._table_names = set()

    def has_tables(self) -> bool:
        return bool(self._table_names)

    def table_names(self):
        return sorted(self._table_names)

    def reset(self):
        """Drops every table so a fresh upload session can start clean."""
        with self._engine.begin() as connection:
            for table_name in list(self._table_names):
                connection.exec_driver_sql(f'DROP TABLE IF EXISTS "{table_name}"')
        self._table_names.clear()

    def load_file(self, path: str) -> list:
        """Loads a CSV or XLSX file into one or more tables. Returns the list of table names created."""
        extension = Path(path).suffix.lower()
        created = []
        if extension == ".csv":
            df = pd.read_csv(path)
            table_name = self._unique_table_name(Path(path).stem)
            self._write_table(table_name, df)
            created.append(table_name)
        elif extension in (".xlsx", ".xls"):
            sheets = pd.read_excel(path, sheet_name=None)
            for sheet_name, df in sheets.items():
                if df is None or df.empty:
                    continue
                table_name = self._unique_table_name(sheet_name)
                self._write_table(table_name, df)
                created.append(table_name)
        else:
            raise ValueError(f"Unsupported structured file type: {extension}")

        if not created:
            raise ValueError(f"No data found in '{os.path.basename(path)}'.")
        return created

    def _write_table(self, table_name: str, df: pd.DataFrame):
        df = df.copy()
        df.columns = [self._sanitize_identifier(str(col)) for col in df.columns]
        # Pandas infers per-column dtypes for us; to_sql maps them to
        # native SQLite column types automatically.
        df.to_sql(table_name, self._engine, if_exists="replace", index=False)
        self._table_names.add(table_name)

    def _unique_table_name(self, raw_name: str) -> str:
        base = self._sanitize_identifier(raw_name)
        name = base
        counter = 2
        while name in self._table_names:
            name = f"{base}_{counter}"
            counter += 1
        return name

    @staticmethod
    def _sanitize_identifier(name: str) -> str:
        cleaned = re.sub(r"[^0-9a-zA-Z_]+", "_", name.strip()).strip("_").lower()
        if not cleaned:
            cleaned = "table"
        if cleaned[0].isdigit():
            cleaned = f"t_{cleaned}"
        return cleaned

    def describe(self) -> str:
        return "Uploaded Files"
