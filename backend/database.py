import sqlite3
from pathlib import Path

DATABASE_PATH = Path(__file__).resolve().parent.parent / "data" / "inventory.db"


def get_connection():
    if not DATABASE_PATH.exists():
        raise FileNotFoundError(
            "Inventory database was not found. Run scripts/create_database.py "
            "and scripts/import_data.py before starting the API."
        )

    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection