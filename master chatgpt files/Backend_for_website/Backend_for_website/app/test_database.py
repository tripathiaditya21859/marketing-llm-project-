
from app.config import DATABASE_PATH
from app.database_backend import get_connection


def test_database():

    print("\n===== MOSETA DATABASE TEST =====")

    print("Database location:")
    print(DATABASE_PATH)

    print("\nDatabase exists:")
    print(DATABASE_PATH.exists())

    conn = get_connection()

    try:
        tables = conn.execute("""
            SELECT name
            FROM sqlite_master
            WHERE type = 'table'
            ORDER BY name
        """).fetchall()

        print("\nExisting database tables:")

        for table in tables:
            print("-", table["name"])

        print("\nTotal tables:", len(tables))

        user_count = conn.execute(
            "SELECT COUNT(*) FROM users"
        ).fetchone()[0]

        print("Total users:", user_count)

        print("\nDATABASE CONNECTION SUCCESSFUL!")

    finally:
        conn.close()


if __name__ == "__main__":
    test_database()
