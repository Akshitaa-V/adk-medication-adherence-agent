"""SQLite data source for the agent.

The database is built from data/seed.sql on first use. Point MED_DB_PATH at
another file to use your own (synthetic) data.
"""

import os
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SEED_FILE = ROOT / "data" / "seed.sql"
DEFAULT_DB = ROOT / "data" / "medications.db"


def get_connection() -> sqlite3.Connection:
    db_path = Path(os.getenv("MED_DB_PATH", DEFAULT_DB))
    is_new = not db_path.exists()
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    if is_new:
        conn.executescript(SEED_FILE.read_text(encoding="utf-8"))
        conn.commit()
    return conn
