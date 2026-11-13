
import sqlite3
import hashlib
import secrets
import getpass

from database import get_connection


def hash_password(password):
    salt = secrets.token_bytes(16)
    iterations = 600000

    password_hash = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        iterations
    )

    return (
        f"pbkdf2_sha256${iterations}$"
        f"{salt.hex()}${password_hash.hex()}"
    )


def create_superadmin():

    conn = get_connection()
    cursor = conn.cursor()

    try:
        print("\n===== MOSETA SUPER ADMIN SETUP =====\n")

        full_name = input("Enter Super Admin name: ").strip()
        email = input("Enter Super Admin email: ").strip().lower()

        if not full_name or not email or "@" not in email:
            print("Invalid name or email.")
            return

        existing = cursor.execute("""
            SELECT id FROM users
            WHERE email = ? AND organization_id IS NULL
        """, (email,)).fetchone()

        if existing:
            print("This Super Admin email already exists.")
            return

        password = getpass.getpass("Create password: ")
        confirm_password = getpass.getpass("Confirm password: ")

        if len(password) < 12:
            print("Password must contain at least 12 characters.")
            return

        if password != confirm_password:
            print("Passwords do not match.")
            return

        password_hash = hash_password(password)

        cursor.execute("""
            INSERT INTO users (
                organization_id,
                full_name,
                email,
                password_hash,
                is_platform_superadmin,
                status
            )
            VALUES (NULL, ?, ?, ?, 1, 'active')
        """, (full_name, email, password_hash))

        user_id = cursor.lastrowid

        role = cursor.execute("""
            SELECT id FROM roles
            WHERE role_name = 'Super Admin'
            AND scope = 'platform'
            AND organization_id IS NULL
        """).fetchone()

        if not role:
            raise ValueError("Platform Super Admin role not found.")

        role_id = role["id"]

        cursor.execute("""
            INSERT INTO user_roles (user_id, role_id)
            VALUES (?, ?)
        """, (user_id, role_id))

        # Give the platform Super Admin all current permissions
        cursor.execute("""
            INSERT OR IGNORE INTO role_permissions
            (role_id, permission_id)
            SELECT ?, id FROM permissions
        """, (role_id,))

        conn.commit()

        print("\nSuper Admin created successfully!")
        print("User ID:", user_id)
        print("Email:", email)
        print("Role: Super Admin")

    except (sqlite3.Error, ValueError) as error:
        conn.rollback()
        print("Error creating Super Admin:", error)

    finally:
        conn.close()


if __name__ == "__main__":
    create_superadmin()

#role --> super admin
