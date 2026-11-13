
from database import get_connection

def inspect_database():

    conn = get_connection()
    cursor = conn.cursor()

    try:
        print("\n========== DATABASE TABLES ==========\n")

        cursor.execute("""
            SELECT name
            FROM sqlite_master
            WHERE type = 'table'
            ORDER BY name
        """)

        tables = [row[0] for row in cursor.fetchall()]

        for table in tables:
            print("-", table)

        # Inspect important RBAC tables
        important_tables = [
            "organizations",
            "users",
            "roles",
            "user_roles",
            "permissions",
            "role_permissions"
        ]

        for table in important_tables:

            print(f"\n========== {table.upper()} ==========\n")

            if table not in tables:
                print("TABLE DOES NOT EXIST")
                continue

            cursor.execute(f"PRAGMA table_info({table})")

            columns = cursor.fetchall()

            print("COLUMNS:")

            for col in columns:
                print({
                    "name": col[1],
                    "type": col[2],
                    "required": bool(col[3]),
                    "primary_key": bool(col[5])
                })

            # Display role names only, not user credentials.
            if table == "roles":
                cursor.execute("SELECT * FROM roles")
                print("\nEXISTING ROLES:")

                for row in cursor.fetchall():
                    print(row)

        print("\n========== INSPECTION COMPLETE ==========\n")

    finally:
        conn.close()


if __name__ == "__main__":
    inspect_database()
    