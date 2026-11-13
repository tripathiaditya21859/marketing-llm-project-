"""Creates / upgrades the tables used by the knowledge base, campaigns and leads pages."""
from app.config import MOSETA_AI_DIR
from app.database_backend import get_connection


def _columns(conn, table):
    return {r["name"] for r in conn.execute(f'PRAGMA table_info("{table}")')}


def ensure_schema():
    conn = get_connection()
    try:
        conn.execute(
            """CREATE TABLE IF NOT EXISTS chat_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT, organization_id INTEGER,
                user_id INTEGER NOT NULL, question TEXT NOT NULL, answer TEXT NOT NULL,
                is_campaign INTEGER DEFAULT 0, platforms TEXT, sources TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP)"""
        )
        # Knowledge base items: uploaded files and typed notes.
        # organization_id NULL = platform (global) knowledge base.
        conn.execute(
            """CREATE TABLE IF NOT EXISTS kb_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                organization_id INTEGER,
                kind TEXT NOT NULL CHECK(kind IN ('file','note')),
                title TEXT NOT NULL,
                file_path TEXT,
                content TEXT,
                size_bytes INTEGER DEFAULT 0,
                created_by INTEGER,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (organization_id) REFERENCES organizations(id))"""
        )
        cols = _columns(conn, "campaigns")
        for name, ddl in (("message", "TEXT"), ("subject", "TEXT"),
                          ("channel", "TEXT"), ("total_recipients", "INTEGER DEFAULT 0"),
                          ("created_by", "INTEGER")):
            if name not in cols:
                conn.execute(f"ALTER TABLE campaigns ADD COLUMN {name} {ddl}")
        conn.execute(
            """CREATE TABLE IF NOT EXISTS campaign_recipients (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                campaign_id INTEGER NOT NULL,
                organization_id INTEGER NOT NULL,
                name TEXT, phone TEXT, email TEXT,
                channel TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'queued',
                detail TEXT,
                sent_at DATETIME,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (campaign_id) REFERENCES campaigns(id),
                FOREIGN KEY (organization_id) REFERENCES organizations(id))"""
        )
        conn.execute("CREATE INDEX IF NOT EXISTS idx_recipients_campaign ON campaign_recipients(campaign_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_recipients_org ON campaign_recipients(organization_id)")
        conn.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_users_email_lower ON users (LOWER(email))")

        # Register platform PDFs already in product_docs as global KB items.
        docs = MOSETA_AI_DIR / "product_docs"
        if docs.exists():
            known = {r["file_path"] for r in conn.execute(
                "SELECT file_path FROM kb_items WHERE organization_id IS NULL AND kind='file'")}
            for f in sorted(docs.glob("*.pdf")):
                if str(f) not in known:
                    conn.execute(
                        "INSERT INTO kb_items (organization_id, kind, title, file_path, size_bytes) "
                        "VALUES (NULL,'file',?,?,?)", (f.name, str(f), f.stat().st_size))
        conn.commit()
    finally:
        conn.close()
