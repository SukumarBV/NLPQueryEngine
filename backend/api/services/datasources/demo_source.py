import os
import tempfile

from .demo_data import build_demo_database
from .sqlite_source import SQLiteDataSource

_DEMO_DB_PATH = os.path.join(tempfile.gettempdir(), "nlp-query-engine-demo.db")


class DemoDataSource(SQLiteDataSource):
    """
    Built-in sample dataset (employees, departments, customers, products,
    orders, sales) so the app is usable with zero setup. Generated once
    per host (offline, no network calls) and reused on subsequent
    "Use Demo" clicks.
    """

    def __init__(self):
        if not os.path.exists(_DEMO_DB_PATH):
            build_demo_database(_DEMO_DB_PATH)
        super().__init__(_DEMO_DB_PATH)

    def describe(self) -> str:
        return "Demo Database"
