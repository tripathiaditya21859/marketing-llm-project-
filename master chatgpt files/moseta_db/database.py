import sqlite3
from pathlib import Path

# Always locate database relative to this file
BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "moseta.db"


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def check_database():
    try:
        conn = get_connection()
        conn.execute("SELECT 1")
        conn.close()
        print("Moseta database connected successfully!")
        return True

    except sqlite3.Error as e:
        print("Database connection failed:", e)
        return False


if __name__ == "__main__":
    check_database()