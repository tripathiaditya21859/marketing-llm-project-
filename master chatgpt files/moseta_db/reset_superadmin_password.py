
import getpass

from database import get_connection
from auth_service import hash_password


def reset_superadmin_password():

    print("\n===== MOSETA AI PASSWORD RESET =====\n")

    password = getpass.getpass("Enter new Super Admin password: ")
    confirm_password = getpass.getpass("Confirm new password: ")

    if not password:
        print("Password cannot be empty.")
        return

    if password != confirm_password:
        print("Passwords do not match.")
        return

    if len(password) < 12:
        print("Use a password with at least 12 characters.")
        return

    # Generate secure password hash
    new_hash = hash_password(password)

    conn = get_connection()

    try:
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE users
            SET password_hash = ?
            WHERE id = 1
            AND is_platform_superadmin = 1
        """, (new_hash,))

        if cursor.rowcount == 0:
            print("Super Admin account not found.")
            conn.rollback()
            return

        conn.commit()

        print("\nPassword updated successfully!")
        print("Super Admin User ID: 1")
        print("You can now log in using your new password.")

    except Exception as error:
        conn.rollback()
        print("Error:", error)

    finally:
        conn.close()



if __name__ == "__main__":
    reset_superadmin_password()
