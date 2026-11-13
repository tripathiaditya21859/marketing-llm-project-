
import hashlib
import secrets
import sqlite3
from datetime import datetime, timedelta, timezone

from database import get_connection


# ==========================================
# MOSЕTA AI - COMPANY ADMIN MANAGEMENT
# ==========================================

ADMIN_ROLE = "company_admin"
INVITATION_VALIDITY_HOURS = 48
PBKDF2_ITERATIONS = 310000


# ==========================================
# DATABASE HELPERS
# ==========================================

def get_columns(cursor, table):
    cursor.execute(f"PRAGMA table_info({table})")
    return {row[1]: row for row in cursor.fetchall()}


def find_column(columns, candidates):
    for candidate in candidates:
        if candidate in columns:
            return candidate
    return None


def row_to_dict(cursor, row):
    return dict(zip([col[0] for col in cursor.description], row))


def initialize_admin_tables():
    """Create the invitation table."""

    conn = get_connection()

    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS admin_invitations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                organization_id INTEGER NOT NULL,
                full_name TEXT NOT NULL,
                email TEXT NOT NULL,
                token_hash TEXT NOT NULL UNIQUE,
                expires_at TEXT NOT NULL,
                status TEXT DEFAULT 'pending',
                invited_by INTEGER,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        conn.commit()
        print("Admin invitation table initialized successfully!")

    finally:
        conn.close()


# ==========================================
# PASSWORD SECURITY
# ==========================================

def hash_password(password):
    salt = secrets.token_bytes(16)

    password_hash = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        PBKDF2_ITERATIONS
    )

    return (
        f"pbkdf2_sha256${PBKDF2_ITERATIONS}"
        f"${salt.hex()}${password_hash.hex()}"
    )


def hash_token(token):
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


# ==========================================
# ROLE MANAGEMENT
# ==========================================

def get_admin_role_id(cursor):
    columns = get_columns(cursor, "roles")

    role_column = find_column(
        columns, ["role_name", "name", "role"]
    )

    if not role_column:
        raise ValueError("Could not identify role name column.")

    cursor.execute(
        f"SELECT id FROM roles WHERE LOWER({role_column}) = ?",
        (ADMIN_ROLE,)
    )

    result = cursor.fetchone()

    if not result:
        raise ValueError(
            "Company Admin role not found. "
            "Create the role in your RBAC setup first."
        )

    return result[0]


def assign_admin_role(cursor, user_id, role_id):
    columns = get_columns(cursor, "user_roles")

    user_col = find_column(columns, ["user_id"])
    role_col = find_column(columns, ["role_id"])

    if not user_col or not role_col:
        raise ValueError("Invalid user_roles table structure.")

    cursor.execute(
        f"""
        INSERT INTO user_roles ({user_col}, {role_col})
        VALUES (?, ?)
        """,
        (user_id, role_id)
    )


# ==========================================
# COMPANY ADMIN INVITATION
# ==========================================

def invite_company_admin(
    organization_id,
    full_name,
    email,
    invited_by=None
):
    """
    Super Admin invites an Admin for an approved organization.
    Returns a one-time activation token.
    """

    conn = get_connection()

    try:
        cursor = conn.cursor()

        cursor.execute(
            "SELECT id FROM organizations WHERE id = ?",
            (organization_id,)
        )

        if not cursor.fetchone():
            raise ValueError("Organization does not exist.")

        email = email.strip().lower()

        user_columns = get_columns(cursor, "users")
        email_col = find_column(user_columns, ["email"])

        if not email_col:
            raise ValueError("Users table has no email column.")

        cursor.execute(
            f"SELECT id FROM users WHERE LOWER({email_col}) = ?",
            (email,)
        )

        if cursor.fetchone():
            raise ValueError("This email already has an account.")

        cursor.execute("""
            SELECT id FROM admin_invitations
            WHERE LOWER(email) = ?
            AND status = 'pending'
        """, (email,))

        if cursor.fetchone():
            raise ValueError("A pending invitation already exists.")

        token = secrets.token_urlsafe(32)
        token_digest = hash_token(token)

        expiry = (
            datetime.now(timezone.utc)
            + timedelta(hours=INVITATION_VALIDITY_HOURS)
        ).isoformat()

        cursor.execute("""
            INSERT INTO admin_invitations (
                organization_id,
                full_name,
                email,
                token_hash,
                expires_at,
                status,
                invited_by
            )
            VALUES (?, ?, ?, ?, ?, 'pending', ?)
        """, (
            organization_id,
            full_name.strip(),
            email,
            token_digest,
            expiry,
            invited_by
        ))

        conn.commit()

        print("Admin invitation created successfully!")
        print("Email:", email)
        print("Organization ID:", organization_id)

        # Send this token through an email integration later.
        return token

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()


# ==========================================
# ACTIVATE COMPANY ADMIN
# ==========================================

def activate_company_admin(token, password):
    """
    Admin activates their account using an invitation token.
    """

    if len(password) < 10:
        raise ValueError("Password must contain at least 10 characters.")

    conn = get_connection()

    try:
        cursor = conn.cursor()

        cursor.execute("""
            SELECT *
            FROM admin_invitations
            WHERE token_hash = ?
            AND status = 'pending'
        """, (hash_token(token),))

        invitation = cursor.fetchone()

        if not invitation:
            raise ValueError("Invalid or already used invitation.")

        invitation = row_to_dict(cursor, invitation)

        expiry = datetime.fromisoformat(invitation["expires_at"])

        if expiry <= datetime.now(timezone.utc):
            cursor.execute("""
                UPDATE admin_invitations
                SET status = 'expired'
                WHERE id = ?
            """, (invitation["id"],))

            conn.commit()
            raise ValueError("Invitation has expired.")

        # Inspect the existing users schema.
        columns = get_columns(cursor, "users")

        values = {}

        candidates = {
            "organization_id": ["organization_id"],
            "full_name": ["full_name", "name"],
            "email": ["email"],
            "password_hash": ["password_hash", "hashed_password"],
            "password": ["password"],
            "status": ["status"],
            "is_active": ["is_active"],
            "created_at": ["created_at"]
        }

        values["organization_id"] = invitation["organization_id"]
        values["full_name"] = invitation["full_name"]
        values["email"] = invitation["email"]

        password_col = find_column(
            columns, ["password_hash", "hashed_password", "password"]
        )

        if not password_col:
            raise ValueError(
                "Users table needs a password hash column."
            )

        values[password_col] = hash_password(password)

        if "status" in columns:
            values["status"] = "active"

        if "is_active" in columns:
            values["is_active"] = 1

        if "created_at" in columns:
            values["created_at"] = datetime.now(
                timezone.utc
            ).isoformat()

        # Identify missing mandatory columns before inserting.
        for name, info in columns.items():
            not_null = info[3]
            has_default = info[4] is not None
            is_primary_key = info[5]

            if (
                not_null
                and not has_default
                and not is_primary_key
                and name not in values
            ):
                raise ValueError(
                    f"Users table has an additional required column: {name}. "
                    "Update the activation mapping before proceeding."
                )

        insert_columns = list(values.keys())
        placeholders = ", ".join(["?"] * len(insert_columns))
        column_names = ", ".join(insert_columns)

        cursor.execute(
            f"""
            INSERT INTO users ({column_names})
            VALUES ({placeholders})
            """,
            [values[col] for col in insert_columns]
        )

        user_id = cursor.lastrowid

        # Assign Company Admin RBAC role.
        role_id = get_admin_role_id(cursor)

        assign_admin_role(cursor, user_id, role_id)

        # Consume invitation.
        cursor.execute("""
            UPDATE admin_invitations
            SET status = 'accepted'
            WHERE id = ?
        """, (invitation["id"],))

        conn.commit()

        return {
            "success": True,
            "user_id": user_id,
            "organization_id": invitation["organization_id"],
            "email": invitation["email"],
            "role": ADMIN_ROLE
        }

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()


# ==========================================
# VIEW COMPANY ADMINS
# ==========================================

def get_company_admins(organization_id=None):
    conn = get_connection()

    try:
        cursor = conn.cursor()

        role_id = get_admin_role_id(cursor)

        query = """
            SELECT
                u.id,
                u.organization_id,
                u.full_name,
                u.email,
                u.status,
                u.created_at
            FROM users u
            INNER JOIN user_roles ur
                ON ur.user_id = u.id
            WHERE ur.role_id = ?
        """

        params = [role_id]

        if organization_id is not None:
            query += " AND u.organization_id = ?"
            params.append(organization_id)

        cursor.execute(query, params)

        return [
            row_to_dict(cursor, row)
            for row in cursor.fetchall()
        ]

    finally:
        conn.close()


# ==========================================
# ACTIVATE / SUSPEND ADMIN
# ==========================================

def update_admin_status(user_id, new_status):
    if new_status not in ["active", "suspended"]:
        raise ValueError("Invalid account status.")

    conn = get_connection()

    try:
        cursor = conn.cursor()

        columns = get_columns(cursor, "users")

        status_col = find_column(
            columns, ["status", "account_status"]
        )

        if not status_col:
            raise ValueError(
                "Users table has no status column."
            )

        role_id = get_admin_role_id(cursor)

        cursor.execute("""
            SELECT u.id
            FROM users u
            INNER JOIN user_roles ur ON ur.user_id = u.id
            WHERE u.id = ? AND ur.role_id = ?
        """, (user_id, role_id))

        if not cursor.fetchone():
            raise ValueError("Company Admin account not found.")

        cursor.execute(
            f"UPDATE users SET {status_col} = ? WHERE id = ?",
            (new_status, user_id)
        )

        conn.commit()

        print(f"Admin account {new_status} successfully!")

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()


# ==========================================
# TEST / COMMAND LINE
# ==========================================

if __name__ == "__main__":
    initialize_admin_tables()

    print("\nMOSЕTA AI ADMIN MANAGEMENT")
    print("1. List all Company Admins")
    print("2. List Admins of an Organization")
    print("3. Suspend Admin")
    print("4. Reactivate Admin")

    choice = input("\nSelect option: ").strip()

    try:
        if choice == "1":
            print(get_company_admins())

        elif choice == "2":
            org_id = int(input("Enter Organization ID: "))
            print(get_company_admins(org_id))

        elif choice == "3":
            user_id = int(input("Enter Admin User ID: "))
            update_admin_status(user_id, "suspended")

        elif choice == "4":
            user_id = int(input("Enter Admin User ID: "))
            update_admin_status(user_id, "active")

        else:
            print("Invalid option.")

    except Exception as error:
        print("Error:", error)
