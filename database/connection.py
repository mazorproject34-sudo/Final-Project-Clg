"""
Database connection manager for SQLite.
Will be implemented to provide database sessions/connections.
"""

import sqlite3
from pathlib import Path

# Path to the SQLite database (not created yet)
DB_PATH = Path(__file__).resolve().parent / "disaster_platform.db"


def get_db_connection():
    """Placeholder for database connection retriever."""
    pass
