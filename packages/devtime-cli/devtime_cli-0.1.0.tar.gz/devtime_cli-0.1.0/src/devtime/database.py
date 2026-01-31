import sqlite3

DB_PATH = "devtime.db"


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """
    CREATE TABLE IF NOT EXISTS sessions (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      task TEXT NOT NULL,
      start_time TEXT NOT NULL,
      end_time TEXT
    )
    """
    )
    return conn
