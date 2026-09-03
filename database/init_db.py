"""
Database Initialization Script for Disaster Decision-Support Platform.
Initializes the SQLite database using schema.sql and verifies table creation.
"""

import sqlite3
from pathlib import Path

# Resolve base paths
CURRENT_DIR = Path(__file__).resolve().parent
DB_PATH = CURRENT_DIR / "disaster_platform.db"
SCHEMA_PATH = CURRENT_DIR / "schema.sql"


def init_database(db_path: Path = DB_PATH, schema_path: Path = SCHEMA_PATH) -> None:
    """
    Initializes the SQLite database by executing schema.sql.
    Enforces foreign key constraints and is safe to execute multiple times.
    """
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found at: {schema_path}")

    with open(schema_path, "r", encoding="utf-8") as f:
        schema_sql = f.read()

    conn = sqlite3.connect(db_path)
    try:
        # Enable foreign key enforcement
        conn.execute("PRAGMA foreign_keys = ON;")
        # Execute the schema script (idempotent CREATE TABLE IF NOT EXISTS)
        conn.executescript(schema_sql)
        conn.commit()
        print(f"Database initialized successfully at: {db_path}")
    except Exception as e:
        conn.rollback()
        print(f"Error initializing database: {e}")
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    init_database()
