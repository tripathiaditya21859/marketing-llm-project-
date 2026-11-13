"""Super Admin only: view and download every account and company stored in the database.

Passwords are never exposed (only a yes/no 'has password' is implied). Anyone who is not the
platform Super Admin gets 403.
"""
from fastapi import APIRouter, Depends, HTTPException, Response

from app.database_backend import get_connection
from app.dependencies import get_current_user
from app.services.excel import build_workbook

router = APIRouter()
XLSX = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


def superadmin_only(user=Depends(get_current_user)):
    if not user["is_superadmin"]:
        raise HTTPException(status_code=403, detail="Only Super Admin can access this.")
    return user


def _users(conn):
    return conn.execute(
        """SELECT u.id, u.full_name, u.email, u.status, u.created_at,
                  u.organization_id, o.company_name,
                  CASE WHEN u.is_platform_superadmin = 1 THEN 'Super Admin'
                       ELSE COALESCE((SELECT GROUP_CONCAT(r.role_name, ', ') FROM user_roles ur
                                      JOIN roles r ON r.id = ur.role_id WHERE ur.user_id = u.id), '') END AS role
           FROM users u LEFT JOIN organizations o ON o.id = u.organization_id
           ORDER BY u.id""").fetchall()


def _companies(conn):
    return conn.execute(
        """SELECT o.id, o.company_name, o.company_email, o.status, o.created_at,
                  (SELECT COUNT(*) FROM users u WHERE u.organization_id = o.id) AS users,
                  (SELECT COUNT(*) FROM campaigns c WHERE c.organization_id = o.id AND c.channel IS NOT NULL) AS campaigns,
                  (SELECT COUNT(*) FROM leads l WHERE l.organization_id = o.id) AS contacts,
                  (SELECT COUNT(*) FROM campaign_recipients r WHERE r.organization_id = o.id AND r.status='sent') AS sent,
                  (SELECT COUNT(*) FROM campaign_recipients r WHERE r.organization_id = o.id AND r.status='failed') AS failed,
                  (SELECT COUNT(*) FROM kb_items k WHERE k.organization_id = o.id) AS knowledge_items,
                  (SELECT COUNT(*) FROM chat_history h WHERE h.organization_id = o.id) AS ai_chats
           FROM organizations o ORDER BY o.id""").fetchall()


@router.get("/users")
def list_users(user=Depends(superadmin_only)):
    conn = get_connection()
    try:
        return {"items": [dict(r) for r in _users(conn)]}
    finally:
        conn.close()


@router.get("/export.xlsx")
def export_everything(user=Depends(superadmin_only)):
    conn = get_connection()
    try:
        users, companies = _users(conn), _companies(conn)
    finally:
        conn.close()
    data = build_workbook({
        "Users": (["User ID", "Name", "Email", "Role", "Company ID", "Company", "Status", "Joined (UTC)"],
                  [(r["id"], r["full_name"], r["email"], r["role"], r["organization_id"], r["company_name"],
                    r["status"], r["created_at"]) for r in users]),
        "Companies": (["Company ID", "Company", "Email", "Status", "Created (UTC)", "Users", "Campaigns",
                       "Contacts", "Messages sent", "Messages failed", "Knowledge items", "AI chats"],
                      [(r["id"], r["company_name"], r["company_email"], r["status"], r["created_at"], r["users"],
                        r["campaigns"], r["contacts"], r["sent"], r["failed"], r["knowledge_items"], r["ai_chats"])
                       for r in companies]),
    })
    return Response(data, media_type=XLSX,
                    headers={"Content-Disposition": "attachment; filename=moseta_accounts.xlsx"})
