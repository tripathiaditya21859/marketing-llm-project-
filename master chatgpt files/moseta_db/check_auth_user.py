
import getpass
from database import get_connection
from auth_service import verify_password

email = input("Enter Super Admin email: ").strip()
password = getpass.getpass("Enter Super Admin password: ")

conn = get_connection()

try:
    cursor = conn.cursor()

    print("\n--- DATABASE CHECK ---")
    print(cursor.execute("PRAGMA database_list").fetchall())

    cursor.execute("""
        SELECT
            id,
            email,
            password_hash,
            is_platform_superadmin,
            status,
            organization_id
        FROM users
        WHERE LOWER(email) = LOWER(?)
    """, (email,))

    user = cursor.fetchone()

    if not user:
        print("\nRESULT: EMAIL NOT FOUND IN THIS DATABASE")

    else:
        print("\n--- USER RECORD CHECK ---")
        print("User ID:", user[0])
        print("Email:", user[1])
        print("Super Admin:", bool(user[3]))
        print("Status:", user[4])
        print("Organization ID:", user[5])

        stored_hash = user[2]

        print("\n--- PASSWORD HASH CHECK ---")
        print("Hash exists:", bool(stored_hash))
        print("Hash format:", stored_hash.split("$")[0]
              if stored_hash else "Missing")

        password_matches = verify_password(
            password, stored_hash
        )

        print("Password matches:", password_matches)

finally:
    conn.close()
