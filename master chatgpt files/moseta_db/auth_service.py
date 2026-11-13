
import hashlib
import hmac
import secrets

from database import get_connection


# 1. PASSWORD HASHING

def hash_password(password):
    """Securely hash password using PBKDF2-SHA256."""

    salt = secrets.token_hex(16)

    password_hash = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        600000
    ).hex()

    return f"pbkdf2_sha256$600000${salt}${password_hash}"



# 2. PASSWORD VERIFICATION

def verify_password(password, stored_hash):
    """Verify password against stored PBKDF2 hash."""

    try:
        algorithm, iterations, salt, expected_hash = (
            stored_hash.split("$")
        )

        if algorithm != "pbkdf2_sha256":
            return False

        calculated_hash = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt.encode("utf-8"),
            int(iterations)
        ).hex()

        return hmac.compare_digest(
            calculated_hash,
            expected_hash
        )

    except (ValueError, TypeError, AttributeError):
        return False


# 3. AUTHENTICATE USER


def authenticate_user(email, password):

    conn = get_connection()

    try:
        cursor = conn.cursor()

        
        # STEP 1: FIND USER
    

        cursor.execute("""
            SELECT
                id,
                organization_id,
                full_name,
                email,
                password_hash,
                is_platform_superadmin,
                status
            FROM users
            WHERE LOWER(email) = LOWER(?)
        """, (email.strip(),))

        user = cursor.fetchone()

        if not user:
            raise ValueError("Invalid email or password.")

        user_id = user[0]
        organization_id = user[1]
        full_name = user[2]
        user_email = user[3]
        stored_hash = user[4]
        is_superadmin = bool(user[5])
        status = user[6]

        
        # STEP 2: VERIFY PASSWORD
        

        if not verify_password(password, stored_hash):
            raise ValueError("Invalid email or password.")

        
        # STEP 3: CHECK USER STATUS
       

        if str(status).lower() != "active":
            raise ValueError(
                "Your account is inactive or suspended."
            )

        
        # STEP 4: SUPER ADMIN AUTHENTICATION
       

        if is_superadmin:

            cursor.execute("""
                SELECT permission_key
                FROM permissions
                WHERE id IN (
                    SELECT permission_id
                    FROM role_permissions
                    WHERE role_id IN (
                        SELECT id
                        FROM roles
                        WHERE LOWER(role_name) = 'super admin'
                        AND scope = 'platform'
                    )
                )
            """)

            role_names = ["Super Admin"]

        else:

            
            # STEP 5: ORGANIZATION VALIDATION
            

            if organization_id is None:
                raise ValueError(
                    "User organization is not configured."
                )

            cursor.execute("""
                SELECT status
                FROM organizations
                WHERE id = ?
            """, (organization_id,))

            organization = cursor.fetchone()

            if not organization:
                raise ValueError("Organization not found.")

            organization_status = str(
                organization[0]
            ).lower()

            if organization_status not in (
                "active", "approved"
            ):
                raise ValueError(
                    "Your organization is not active."
                )

            
            # STEP 6: FETCH USER ROLES
            

            cursor.execute("""
                SELECT
                    r.id,
                    r.role_name,
                    r.scope
                FROM user_roles ur

                JOIN roles r
                    ON ur.role_id = r.id

                WHERE ur.user_id = ?

                AND r.scope = 'organization'

                AND (
                    r.organization_id IS NULL
                    OR r.organization_id = ?
                )

            """, (user_id, organization_id))

            roles = cursor.fetchall()

            if not roles:
                raise ValueError(
                    "No valid role assigned to this user."
                )

            role_names = [
                role[1] for role in roles
            ]

            
            # STEP 7: FETCH ROLE PERMISSIONS
            

            role_ids = [
                role[0] for role in roles
            ]

            placeholders = ",".join(
                "?" for _ in role_ids
            )

            cursor.execute(f"""
                SELECT DISTINCT p.permission_key

                FROM permissions p

                JOIN role_permissions rp
                    ON p.id = rp.permission_id

                WHERE rp.role_id IN ({placeholders})

            """, role_ids)

       
        # STEP 8: COLLECT PERMISSIONS
        

        permissions = [
            row[0] for row in cursor.fetchall()
        ]

       
        # STEP 9: RETURN AUTHENTICATED USER
       

        return {
            "authenticated": True,
            "user_id": user_id,
            "name": full_name,
            "email": user_email,
            "organization_id": organization_id,
            "role": role_names,
            "permissions": permissions,
            "is_superadmin": is_superadmin
        }

    finally:
        conn.close()


# 4. CHECK PERMISSION
def has_permission(user, permission_key):

    if not user or not user.get("authenticated"):
        return False

    # Super Admin has platform-level access
    if user.get("is_superadmin"):
        return True

    return permission_key in user.get(
        "permissions", []
    )

# 5. GET USER PROFILE

def get_user_profile(user_id):

    conn = get_connection()

    try:
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                id,
                full_name,
                email,
                organization_id,
                status,
                created_at
            FROM users
            WHERE id = ?
        """, (user_id,))

        user = cursor.fetchone()

        if not user:
            return None

        return {
            "user_id": user[0],
            "name": user[1],
            "email": user[2],
            "organization_id": user[3],
            "status": user[4],
            "created_at": user[5]
        }

    finally:
        conn.close()


# 6. COMMAND LINE LOGIN TEST

if __name__ == "__main__":

    import getpass

    print("\n========== MOSETA AI LOGIN ==========\n")

    email = input("Enter email: ").strip()
    password = getpass.getpass("Enter password: ")

    try:

        result = authenticate_user(email, password)

        print("\nLOGIN SUCCESSFUL!")
        print("--------------------------------")

        print("User ID:", result["user_id"])
        print("Name:", result["name"])
        print("Email:", result["email"])
        print("Organization:", result["organization_id"])
        print("Role:", result["role"])
        print("Super Admin:", result["is_superadmin"])

        print("\nASSIGNED PERMISSIONS:")

        for permission in result["permissions"]:
            print("-", permission)

        print("\nAuthentication completed successfully.")

    except ValueError as error:

        print("\nLOGIN FAILED:", error)
