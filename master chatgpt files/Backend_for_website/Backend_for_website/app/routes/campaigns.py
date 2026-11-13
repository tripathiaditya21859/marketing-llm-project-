"""Campaigns: upload an Excel/CSV of contacts, choose a channel, send the message.

Every company only sees its own campaigns. Delivery is recorded per recipient; if the
chosen channel has no provider credentials in .env, recipients are recorded as
'not_sent' (nothing is pretended to be delivered).
"""
from datetime import datetime, timezone
from urllib.parse import quote

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, Response, UploadFile

from app.database_backend import get_connection
from app.dependencies import require_permission
from app.services import messaging
from app.services.excel import EMAIL_RE, build_workbook, normalize_phone, read_contacts

router = APIRouter()
campaign_permission = require_permission("campaigns.manage")

MAX_SHEET_BYTES = 5 * 1024 * 1024
XLSX = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


def _org_filter(user, alias=""):
    p = f"{alias}." if alias else ""
    if user["is_superadmin"]:
        return "1=1", []
    return f"{p}organization_id = ?", [user["organization_id"]]


def _now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")


@router.get("/channels")
def channels(user=Depends(campaign_permission)):
    return {"channels": [
        {"id": k, "label": v["label"], "needs": v["needs"], "configured": messaging.is_configured(k),
         "required_keys": messaging.REQUIRED_KEYS[k], "missing_keys": messaging.missing_keys(k)}
        for k, v in messaging.CHANNELS.items()]}


@router.get("")
def list_campaigns(user=Depends(campaign_permission)):
    where, params = _org_filter(user, "c")
    conn = get_connection()
    try:
        rows = conn.execute(
            f"""SELECT c.id, c.organization_id, c.campaign_name, c.channel, c.status, c.message,
                       c.total_recipients, c.created_at,
                       SUM(r.status = 'sent') AS sent, SUM(r.status = 'failed') AS failed,
                       SUM(r.status = 'queued') AS queued, SUM(r.status = 'skipped') AS skipped,
                       SUM(r.status = 'not_sent') AS not_sent
                FROM campaigns c LEFT JOIN campaign_recipients r ON r.campaign_id = c.id
                WHERE {where} AND c.channel IS NOT NULL
                GROUP BY c.id ORDER BY c.id DESC LIMIT 200""", params).fetchall()
        return {"items": [dict(r) for r in rows]}
    finally:
        conn.close()


def _deliver(campaign_id: int):
    """Background job: send to every queued recipient and record the outcome."""
    conn = get_connection()
    try:
        camp = conn.execute("SELECT channel, message, subject FROM campaigns WHERE id = ?",
                            (campaign_id,)).fetchone()
        rows = conn.execute("SELECT id, phone, email FROM campaign_recipients "
                            "WHERE campaign_id = ? AND status = 'queued'", (campaign_id,)).fetchall()
        needs = messaging.CHANNELS[camp["channel"]]["needs"]
        for r in rows:
            target = r["phone"] if needs == "phone" else r["email"]
            try:
                ok, detail = messaging.send(camp["channel"], target, camp["message"], camp["subject"] or "")
            except Exception as exc:  # never let one bad row stop the run
                ok, detail = False, f"error: {exc}"[:300]
            conn.execute("UPDATE campaign_recipients SET status = ?, detail = ?, sent_at = ? WHERE id = ?",
                         ("sent" if ok else "failed", detail, _now(), r["id"]))
            conn.commit()
        conn.execute("UPDATE campaigns SET status = 'completed' WHERE id = ?", (campaign_id,))
        conn.commit()
    except Exception:
        conn.execute("UPDATE campaigns SET status = 'failed' WHERE id = ?", (campaign_id,))
        conn.commit()
    finally:
        conn.close()


@router.post("", status_code=201)
async def create_campaign(
    background: BackgroundTasks,
    name: str = Form(..., min_length=2, max_length=120),
    channel: str = Form(...),
    message: str = Form(..., min_length=1, max_length=1500),
    subject: str = Form(default="", max_length=200),
    country_code: str = Form(default="+91", max_length=6),
    consent: bool = Form(default=False),
    file: UploadFile = File(...),
    user=Depends(campaign_permission),
):
    if user["organization_id"] is None:
        raise HTTPException(status_code=403, detail="Sign in with a company account to run campaigns. "
                                                    "The Super Admin account has no company.")
    if channel not in messaging.CHANNELS:
        raise HTTPException(status_code=400, detail="Unknown channel.")
    if not consent:
        raise HTTPException(status_code=400, detail="Confirm that these contacts have agreed to receive messages.")
    fname = (file.filename or "").lower()
    if not fname.endswith((".xlsx", ".csv")):
        raise HTTPException(status_code=400, detail="Upload an Excel (.xlsx) or CSV file.")
    data = await file.read(MAX_SHEET_BYTES + 1)
    if len(data) > MAX_SHEET_BYTES:
        raise HTTPException(status_code=400, detail="The sheet is larger than 5 MB.")
    try:
        contacts, over_limit = read_contacts(data, fname)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception:
        raise HTTPException(status_code=400, detail="Could not read this file. Is it a valid .xlsx or .csv?")

    needs = messaging.CHANNELS[channel]["needs"]
    configured = messaging.is_configured(channel)
    org_id, seen, rows = user["organization_id"], set(), []
    for c in contacts:
        phone = normalize_phone(c["phone"], country_code) if c["phone"] else None
        email = c["email"].lower() if EMAIL_RE.match(c["email"] or "") else None
        key = phone if needs == "phone" else email
        if not key:
            status, detail = "skipped", f"missing or invalid {needs}"
        elif key in seen:
            status, detail = "skipped", "duplicate in sheet"
        else:
            seen.add(key)
            status, detail = ("queued", None) if configured else (
                "not_sent", f"{messaging.CHANNELS[channel]['label']} provider is not configured")
        rows.append((c["name"], phone, email, status, detail))
    if not any(r[3] in ("queued", "not_sent") for r in rows):
        raise HTTPException(status_code=400, detail=f"No valid {needs} values found in the sheet.")

    conn = get_connection()
    try:
        camp_id = conn.execute(
            "INSERT INTO campaigns (organization_id, campaign_name, platform, status, message, subject, "
            "channel, total_recipients, created_by) VALUES (?,?,?,?,?,?,?,?,?)",
            (org_id, name.strip(), messaging.CHANNELS[channel]["label"],
             "running" if configured else "not_sent", message.strip(), subject.strip(), channel,
             len(rows), user["user_id"])).lastrowid
        for n, phone, email, status, detail in rows:
            conn.execute(
                "INSERT INTO campaign_recipients (campaign_id, organization_id, name, phone, email, channel, "
                "status, detail, sent_at) VALUES (?,?,?,?,?,?,?,?,?)",
                (camp_id, org_id, n, phone, email, channel, status, detail,
                 _now() if status in ("skipped", "not_sent") else None))
            # Keep every valid contact in the company's leads list (no duplicates).
            if status != "skipped":
                dup = conn.execute(
                    "SELECT 1 FROM leads WHERE organization_id = ? AND "
                    "((phone IS NOT NULL AND phone = ?) OR (email IS NOT NULL AND LOWER(email) = ?))",
                    (org_id, phone, email)).fetchone()
                if not dup:
                    conn.execute(
                        "INSERT INTO leads (organization_id, customer_name, phone, email, source) "
                        "VALUES (?,?,?,?,?)",
                        (org_id, n or phone or email, phone, email, f"Campaign: {name.strip()}"[:100]))
        conn.execute(
            "INSERT INTO audit_logs (organization_id, user_id, action, entity_type, entity_id) "
            "VALUES (?,?,?,?,?)", (org_id, user["user_id"], "campaign_created", "campaigns", camp_id))
        conn.commit()
    except Exception:
        conn.rollback()
        raise HTTPException(status_code=500, detail="Could not save the campaign.")
    finally:
        conn.close()

    if configured:
        background.add_task(_deliver, camp_id)
    valid = sum(1 for r in rows if r[3] != "skipped")
    return {
        "id": camp_id, "total": len(rows), "valid": valid, "skipped": len(rows) - valid,
        "ignored_over_limit": over_limit, "provider_configured": configured,
        "message": ("Campaign started. Delivery results appear in Leads & Customers." if configured else
                    "Campaign saved, but nothing was sent: this channel's provider is not configured yet. "
                    "Add the credentials to the backend .env file and run the campaign again."),
    }


def _own_campaign(conn, campaign_id, user):
    where, params = _org_filter(user)
    row = conn.execute(f"SELECT * FROM campaigns WHERE id = ? AND {where}", [campaign_id] + params).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Campaign not found.")
    return row


@router.get("/{campaign_id}/export.xlsx")
def export_campaign(campaign_id: int, user=Depends(campaign_permission)):
    conn = get_connection()
    try:
        camp = _own_campaign(conn, campaign_id, user)
        rows = conn.execute(
            "SELECT name, phone, email, channel, status, detail, sent_at FROM campaign_recipients "
            "WHERE campaign_id = ? ORDER BY id", (campaign_id,)).fetchall()
    finally:
        conn.close()
    data = build_workbook({"Delivery log": (
        ["Name", "Phone", "Email", "Channel", "Status", "Detail", "Time (UTC)"],
        [tuple(r) for r in rows])})
    fname = quote(f"campaign_{campaign_id}_delivery.xlsx")
    return Response(data, media_type=XLSX,
                    headers={"Content-Disposition": f"attachment; filename*=UTF-8''{fname}"})
