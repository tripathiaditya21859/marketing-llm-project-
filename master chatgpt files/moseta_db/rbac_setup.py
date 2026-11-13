
from database import get_connection

def setup_rbac():
    conn = get_connection()
    cursor = conn.cursor()

    try:
        # 1. Create Company Admin role if it does not exist
        cursor.execute("""
            SELECT id FROM roles
            WHERE role_name = ?
            AND scope = ?
            AND organization_id IS NULL
        """, ("company_admin", "organization"))

        result = cursor.fetchone()

        if result:
            company_admin_id = result["id"]
            print("Company Admin role already exists.")
        else:
            cursor.execute("""
                INSERT INTO roles (
                    organization_id,
                    role_name,
                    scope
                )
                VALUES (NULL, ?, ?)
            """, ("company_admin", "organization"))

            company_admin_id = cursor.lastrowid
            print("Company Admin role created.")

        # 2. Permissions assigned to Company Admin
        company_admin_permissions = [
            "users.manage",
            "leads.manage",
            "queries.manage",
            "products.manage",
            "pricing.manage",
            "documents.manage",
            "campaigns.manage",
            "audit.view"
        ]

        # 3. Assign permissions
        for permission_key in company_admin_permissions:

            cursor.execute("""
                SELECT id FROM permissions
                WHERE permission_key = ?
            """, (permission_key,))

            permission = cursor.fetchone()

            if not permission:
                print(f"Missing permission: {permission_key}")
                continue

            permission_id = permission["id"]

            cursor.execute("""
                SELECT 1 FROM role_permissions
                WHERE role_id = ?
                AND permission_id = ?
            """, (company_admin_id, permission_id))

            if not cursor.fetchone():
                cursor.execute("""
                    INSERT INTO role_permissions (
                        role_id,
                        permission_id
                    )
                    VALUES (?, ?)
                """, (company_admin_id, permission_id))

        conn.commit()

        print("\nRBAC setup completed successfully!")
        print("Company Admin ID:", company_admin_id)

    except Exception as error:
        conn.rollback()
        print("RBAC setup failed:", error)

    finally:
        conn.close()


if __name__ == "__main__":
    setup_rbac()
