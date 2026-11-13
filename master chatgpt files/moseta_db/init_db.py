from database import get_connection


def initialize_database():

    conn = get_connection()
    cursor = conn.cursor()

    cursor.executescript("""

    CREATE TABLE IF NOT EXISTS organizations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        company_name TEXT NOT NULL,
        company_email TEXT,
        status TEXT DEFAULT 'active',
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        organization_id INTEGER,
        full_name TEXT NOT NULL,
        email TEXT NOT NULL,
        password_hash TEXT NOT NULL,
        is_platform_superadmin INTEGER DEFAULT 0,
        status TEXT DEFAULT 'active',
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,

        FOREIGN KEY (organization_id)
        REFERENCES organizations(id)
    );

    CREATE UNIQUE INDEX IF NOT EXISTS
    unique_org_user_email
    ON users(organization_id, email)
    WHERE organization_id IS NOT NULL;

    CREATE UNIQUE INDEX IF NOT EXISTS
    unique_platform_user_email
    ON users(email)
    WHERE organization_id IS NULL;

    CREATE TABLE IF NOT EXISTS roles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        organization_id INTEGER,
        role_name TEXT NOT NULL,
        scope TEXT NOT NULL,
        FOREIGN KEY (organization_id)
        REFERENCES organizations(id)
    );

    CREATE TABLE IF NOT EXISTS permissions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        permission_key TEXT UNIQUE NOT NULL,
        description TEXT
    );

    CREATE TABLE IF NOT EXISTS role_permissions (
        role_id INTEGER,
        permission_id INTEGER,
        PRIMARY KEY (role_id, permission_id),

        FOREIGN KEY (role_id) REFERENCES roles(id),
        FOREIGN KEY (permission_id) REFERENCES permissions(id)
    );

    CREATE TABLE IF NOT EXISTS user_roles (
        user_id INTEGER,
        role_id INTEGER,
        PRIMARY KEY (user_id, role_id),

        FOREIGN KEY (user_id) REFERENCES users(id),
        FOREIGN KEY (role_id) REFERENCES roles(id)
    );

    CREATE TABLE IF NOT EXISTS leads (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        organization_id INTEGER NOT NULL,
        customer_name TEXT NOT NULL,
        phone TEXT,
        email TEXT,
        source TEXT,
        status TEXT DEFAULT 'new',
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,

        FOREIGN KEY (organization_id)
        REFERENCES organizations(id)
    );

    CREATE TABLE IF NOT EXISTS customer_queries (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        organization_id INTEGER NOT NULL,
        customer_name TEXT,
        query TEXT NOT NULL,
        status TEXT DEFAULT 'pending',
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,

        FOREIGN KEY (organization_id)
        REFERENCES organizations(id)
    );

    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        organization_id INTEGER NOT NULL,
        product_name TEXT NOT NULL,
        description TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,

        FOREIGN KEY (organization_id)
        REFERENCES organizations(id)
    );

    CREATE TABLE IF NOT EXISTS price_lists (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        organization_id INTEGER NOT NULL,
        product_id INTEGER NOT NULL,
        price REAL NOT NULL,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,

        FOREIGN KEY (organization_id)
        REFERENCES organizations(id),
        FOREIGN KEY (product_id)
        REFERENCES products(id)
    );

    CREATE TABLE IF NOT EXISTS documents (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        organization_id INTEGER NOT NULL,
        file_name TEXT NOT NULL,
        file_path TEXT NOT NULL,
        uploaded_at DATETIME DEFAULT CURRENT_TIMESTAMP,

        FOREIGN KEY (organization_id)
        REFERENCES organizations(id)
    );

    CREATE TABLE IF NOT EXISTS campaigns (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        organization_id INTEGER NOT NULL,
        campaign_name TEXT NOT NULL,
        platform TEXT,
        status TEXT DEFAULT 'draft',
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,

        FOREIGN KEY (organization_id)
        REFERENCES organizations(id)
    );

    CREATE TABLE IF NOT EXISTS audit_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        organization_id INTEGER,
        user_id INTEGER,
        action TEXT NOT NULL,
        entity_type TEXT,
        entity_id INTEGER,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,

        FOREIGN KEY (organization_id)
        REFERENCES organizations(id),
        FOREIGN KEY (user_id)
        REFERENCES users(id)
    );

    """)

    # Initial platform-level permissions
    permissions = [
        ("platform.manage", "Manage entire platform"),
        ("organizations.manage", "Manage companies"),
        ("users.manage", "Manage users"),
        ("roles.manage", "Manage roles and permissions"),
        ("leads.manage", "Manage customer leads"),
        ("queries.manage", "Manage customer queries"),
        ("products.manage", "Manage products"),
        ("pricing.manage", "Manage pricing"),
        ("documents.manage", "Manage documents"),
        ("campaigns.manage", "Manage marketing campaigns"),
        ("audit.view", "View audit logs")
    ]

    cursor.executemany("""
        INSERT OR IGNORE INTO permissions
        (permission_key, description)
        VALUES (?, ?)
    """, permissions)

    # Create platform Super Admin role
    cursor.execute("""
        INSERT INTO roles (role_name, scope)
        SELECT 'Super Admin', 'platform'
        WHERE NOT EXISTS (
            SELECT 1 FROM roles
            WHERE role_name = 'Super Admin'
            AND scope = 'platform'
        )
    """)

    conn.commit()
    conn.close()

    print("Moseta database initialized successfully!")


    