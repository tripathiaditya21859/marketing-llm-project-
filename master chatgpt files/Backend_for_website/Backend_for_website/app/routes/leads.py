"""Leads & Customers: contacts plus the delivery log of every campaign (who got what)."""
from fastapi import APIRouter, Depends, Query, Response

from app.database_backend import get_connection
from app.dependencies import require_permission
from app.services.excel import build_workbook

router = APIRouter()
leads_permission = require_permission("leads.manage")
XLSX = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


def _scope(user, col="organization_id"):
    if user["is_superadmin"]:
        return "1=1", []
    return f"{col} = ?", [user["organization_id"]]


def _contacts(user, limit=1000):
    where, params = _scope(user, "organization_id")
    conn = get_connection()
    try:
        return conn.execute(
            f"SELECT id, organization_id, customer_name, phone, email, source, status, created_at "
            f"FROM leads WHERE {where} ORDER BY id DESC LIMIT ?", params + [limit]).fetchall()
    finally:
        conn.close()


def _deliveries(user, campaign_id=None, limit=5000):
    where, params = _scope(user, "r.organization_id")
    if campaign_id:
        where += " AND r.campaign_id = ?"
        params.append(campaign_id)
    conn = get_connection()
    try:
        return conn.execute(
            f"""SELECT r.id, r.organization_id, r.campaign_id, c.campaign_name, r.name, r.phone, r.email,
                       r.channel, r.status, r.detail, r.sent_at
                FROM campaign_recipients r JOIN campaigns c ON c.id = r.campaign_id
                WHERE {where} ORDER BY r.id DESC LIMIT ?""", params + [limit]).fetchall()
    finally:
        conn.close()


@router.get("/contacts")
def contacts(user=Depends(leads_permission)):
    return {"items": [dict(r) for r in _contacts(user, 500)]}


@router.get("/deliveries")
def deliveries(campaign_id: int | None = Query(default=None), user=Depends(leads_permission)):
    return {"items": [dict(r) for r in _deliveries(user, campaign_id, 1000)]}


@router.get("/export.xlsx")
def export_all(user=Depends(leads_permission)):
    c = _contacts(user)
    d = _deliveries(user)
    data = build_workbook({
        "Contacts": (["ID", "Name", "Phone", "Email", "Source", "Status", "Added"],
                     [(r["id"], r["customer_name"], r["phone"], r["email"], r["source"], r["status"],
                       r["created_at"]) for r in c]),
        "Delivery log": (["Campaign", "Name", "Phone", "Email", "Channel", "Status", "Detail", "Time (UTC)"],
                         [(r["campaign_name"], r["name"], r["phone"], r["email"], r["channel"], r["status"],
                           r["detail"], r["sent_at"]) for r in d]),
    })
    return Response(data, media_type=XLSX,
                    headers={"Content-Disposition": "attachment; filename=moseta_leads_and_deliveries.xlsx"})
