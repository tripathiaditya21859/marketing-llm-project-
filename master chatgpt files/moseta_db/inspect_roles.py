
from database import get_connection

conn = get_connection()
cursor = conn.cursor()

tables = ["roles", "permissions", "role_permissions", "user_roles"]

for table in tables:
    print(f"\n========== {table.upper()} ==========")

    cursor.execute(f"SELECT * FROM {table}")
    rows = cursor.fetchall()

    if rows:
        for row in rows:
            print(dict(row))
    else:
        print("No records found.")

conn.close()

