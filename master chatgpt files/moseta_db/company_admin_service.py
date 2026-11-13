
import hashlib
import secrets
import sqlite3
import getpass

from database import get_connection

# PASSWORD SECURITY

def hash_password(password):
    """Hash password using PBKDF2-SHA256."""

    salt = secrets.token_hex(16)

    password_hash = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        600000
    ).hex()

    return f"pbkdf2_sha256$600000${salt}${password_hash}"


# CREATE COMPANY ADMIN

def create_company_admin(
    organization_id,
    full_name,
    email,
    password
):
    conn = get_connection()

    try:
        cursor = conn.cursor()

        # 1. Check organization
        cursor.execute("""
            SELECT id, company_name, status
            FROM organizations
            WHERE id = ?
        """, (organization_id,))

        organization = cursor.fetchone()

        if not organization:
            raise ValueError("Organization does not exist.")

        organization_status = str(organization[2]).lower()

        if organization_status not in ("approved", "active"):
            raise ValueError(
                "Organization must be approved before creating an admin."
            )

        # 2. Check duplicate email
        cursor.execute("""
            SELECT id
            FROM users
            WHERE LOWER(email) = LOWER(?)
        """, (email,))

        if cursor.fetchone():
            raise ValueError("This email is already registered.")

        # 3. Find Company Admin role
        cursor.execute("""
            SELECT id
            FROM roles
            WHERE LOWER(role_name) = 'company_admin'
            AND scope = 'organization'
        """)

        role = cursor.fetchone()

        if not role:
            raise ValueError(
                "Company Admin role not found. Run rbac_setup.py first."
            )

        role_id = role[0]

        # 4. Securely hash password
        password_hash = hash_password(password)

        # 5. Create user
        cursor.execute("""
            INSERT INTO users (
                organization_id,
                full_name,
                email,
                password_hash,
                is_platform_superadmin,
                status
            )
            VALUES (?, ?, ?, ?, 0, 'active')
        """, (
            organization_id,
            full_name.strip(),
            email.strip().lower(),
            password_hash
        ))

        user_id = cursor.lastrowid

        # 6. Assign Company Admin role
        cursor.execute("""
            INSERT INTO user_roles (user_id, role_id)
            VALUES (?, ?)
        """, (user_id, role_id))

        conn.commit()

        print("\nCompany Admin created successfully!")
        print("User ID:", user_id)
        print("Organization ID:", organization_id)
        print("Organization:", organization[1])
        print("Email:", email)
        print("Role: Company Admin")

        return user_id

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()


# LIST COMPANY ADMINS

def get_company_admins(organization_id=None):

    conn = get_connection()

    try:
        cursor = conn.cursor()

        query = """
            SELECT
                u.id,
                u.full_name,
                u.email,
                u.organization_id,
                o.company_name,
                u.status,
                u.created_at
            FROM users u
            JOIN user_roles ur ON u.id = ur.user_id
            JOIN roles r ON ur.role_id = r.id
            JOIN organizations o ON u.organization_id = o.id
            WHERE LOWER(r.role_name) = 'company_admin'
        """

        params = ()

        if organization_id is not None:
            query += " AND u.organization_id = ?"
            params = (organization_id,)

        query += " ORDER BY u.id DESC"

        cursor.execute(query, params)

        admins = cursor.fetchall()

        for admin in admins:
            print({
                "user_id": admin[0],
                "name": admin[1],
                "email": admin[2],
                "organization_id": admin[3],
                "company": admin[4],
                "status": admin[5],
                "created_at": admin[6]
            })

        return admins

    finally:
        conn.close()



# ACTIVATE / SUSPEND COMPANY ADMIN

def update_company_admin_status(user_id, new_status):

    if new_status not in ("active", "suspended"):
        raise ValueError("Invalid status.")

    conn = get_connection()

    try:
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE users
            SET status = ?
            WHERE id = ?
            AND is_platform_superadmin = 0
            AND EXISTS (
                SELECT 1
                FROM user_roles ur
                JOIN roles r ON ur.role_id = r.id
                WHERE ur.user_id = users.id
                AND LOWER(r.role_name) = 'company_admin'
            )
        """, (new_status, user_id))

        if cursor.rowcount == 0:
            raise ValueError("Company Admin not found.")

        conn.commit()

        print(
            f"Company Admin {user_id} status updated to {new_status}."
        )

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()


# ==========================================
# COMMAND LINE MENU
# ==========================================

def main():

    while True:

        print("\n========== MOSETA COMPANY ADMIN ==========")
        print("1. Create Company Admin")
        print("2. View All Company Admins")
        print("3. Suspend Company Admin")
        print("4. Activate Company Admin")
        print("5. Exit")

        choice = input("\nSelect option: ").strip()

        try:

            if choice == "1":

                organization_id = int(
                    input("Enter approved Organization ID: ")
                )

                full_name = input("Enter Admin Name: ").strip()
                email = input("Enter Admin Email: ").strip()

                password = getpass.getpass("Create Password: ")
                confirm_password = getpass.getpass(
                    "Confirm Password: "
                )

                if password != confirm_password:
                    print("Passwords do not match.")
                    continue

                if len(password) < 12:
                    print("Password must be at least 12 characters.")
                    continue

                create_company_admin(
                    organization_id,
                    full_name,
                    email,
                    password
                )

            elif choice == "2":

                get_company_admins()

            elif choice == "3":

                user_id = int(input("Enter Admin User ID: "))

                update_company_admin_status(
                    user_id, "suspended"
                )

            elif choice == "4":

                user_id = int(input("Enter Admin User ID: "))

                update_company_admin_status(
                    user_id, "active"
                )

            elif choice == "5":

                print("Exiting Company Admin Service.")
                break

            else:
                print("Invalid option.")

        except (ValueError, sqlite3.Error) as error:
            print("Error:", error)


if __name__ == "__main__":
    main()
