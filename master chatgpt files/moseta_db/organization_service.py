
from database import get_connection
import sqlite3


def initialize_organization_tables():
    """Create company registration and approval tables."""

    conn = get_connection()
    cursor = conn.cursor()

    cursor.executescript("""
        CREATE TABLE IF NOT EXISTS organization_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company_name TEXT NOT NULL,
            company_email TEXT NOT NULL,
            contact_number TEXT,
            website TEXT,
            industry TEXT,
            business_address TEXT,
            gst_number TEXT,
            applicant_name TEXT NOT NULL,
            applicant_email TEXT NOT NULL,
            applicant_phone TEXT,
            status TEXT NOT NULL DEFAULT 'pending'
                CHECK(status IN ('pending', 'approved', 'rejected')),
            rejection_reason TEXT,
            organization_id INTEGER,
            submitted_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            reviewed_at DATETIME
        );

        CREATE TABLE IF NOT EXISTS organization_approvals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            request_id INTEGER NOT NULL,
            organization_id INTEGER,
            reviewed_by INTEGER NOT NULL,
            decision TEXT NOT NULL
                CHECK(decision IN ('approved', 'rejected')),
            remarks TEXT,
            reviewed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(request_id)
                REFERENCES organization_requests(id),
            FOREIGN KEY(organization_id)
                REFERENCES organizations(id)
        );
    """)

    conn.commit()
    conn.close()

    print("Organization tables initialized successfully!")


def register_company(
    company_name,
    company_email,
    applicant_name,
    applicant_email,
    contact_number=None,
    website=None,
    industry=None,
    business_address=None,
    gst_number=None,
    applicant_phone=None
):
    """Submit a new company registration."""

    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            INSERT INTO organization_requests (
                company_name,
                company_email,
                contact_number,
                website,
                industry,
                business_address,
                gst_number,
                applicant_name,
                applicant_email,
                applicant_phone
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            company_name,
            company_email,
            contact_number,
            website,
            industry,
            business_address,
            gst_number,
            applicant_name,
            applicant_email,
            applicant_phone
        ))

        request_id = cursor.lastrowid
        conn.commit()

        print("Company registration submitted successfully!")
        print("Registration ID:", request_id)

        return request_id

    except sqlite3.Error:
        conn.rollback()
        raise

    finally:
        conn.close()


def get_pending_companies():
    """Return all pending company applications."""

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT *
        FROM organization_requests
        WHERE status = 'pending'
        ORDER BY submitted_at ASC
    """)

    rows = cursor.fetchall()
    columns = [column[0] for column in cursor.description]

    companies = [
        dict(zip(columns, row))
        for row in rows
    ]

    conn.close()
    return companies


def approve_company(request_id, super_admin_id, remarks=None):
    """Approve a company and create its organization."""

    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT *
            FROM organization_requests
            WHERE id = ? AND status = 'pending'
        """, (request_id,))

        request = cursor.fetchone()

        if request is None:
            raise ValueError(
                "Registration not found or already reviewed."
            )

        columns = [column[0] for column in cursor.description]
        company = dict(zip(columns, request))

        # Create organization using the existing organizations schema.
        cursor.execute("PRAGMA table_info(organizations)")
        org_columns = cursor.fetchall()

        available_columns = {
            column[1]: column for column in org_columns
        }

        organization_data = {
            "company_name": company["company_name"],
            "company_email": company["company_email"],
            "status": "active"
        }

        insert_data = {
            key: value
            for key, value in organization_data.items()
            if key in available_columns
        }

        if "company_name" not in insert_data:
            raise ValueError(
                "organizations table must contain company_name."
            )

        names = list(insert_data.keys())
        placeholders = ", ".join(["?"] * len(names))
        column_names = ", ".join(names)

        cursor.execute(
            f"""
            INSERT INTO organizations ({column_names})
            VALUES ({placeholders})
            """,
            tuple(insert_data[name] for name in names)
        )

        organization_id = cursor.lastrowid

        # Update registration.
        cursor.execute("""
            UPDATE organization_requests
            SET status = 'approved',
                organization_id = ?,
                reviewed_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (organization_id, request_id))

        # Save approval history.
        cursor.execute("""
            INSERT INTO organization_approvals (
                request_id,
                organization_id,
                reviewed_by,
                decision,
                remarks
            )
            VALUES (?, ?, ?, 'approved', ?)
        """, (
            request_id,
            organization_id,
            super_admin_id,
            remarks
        ))

        conn.commit()

        print("Company approved successfully!")
        print("Organization ID:", organization_id)

        return organization_id

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()


def reject_company(
    request_id,
    super_admin_id,
    rejection_reason
):
    """Reject a company registration."""

    if not rejection_reason or not rejection_reason.strip():
        raise ValueError("A rejection reason is required.")

    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT id
            FROM organization_requests
            WHERE id = ? AND status = 'pending'
        """, (request_id,))

        if cursor.fetchone() is None:
            raise ValueError(
                "Registration not found or already reviewed."
            )

        cursor.execute("""
            UPDATE organization_requests
            SET status = 'rejected',
                rejection_reason = ?,
                reviewed_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (rejection_reason, request_id))

        cursor.execute("""
            INSERT INTO organization_approvals (
                request_id,
                reviewed_by,
                decision,
                remarks
            )
            VALUES (?, ?, 'rejected', ?)
        """, (
            request_id,
            super_admin_id,
            rejection_reason
        ))

        conn.commit()

        print("Company registration rejected successfully!")

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()



