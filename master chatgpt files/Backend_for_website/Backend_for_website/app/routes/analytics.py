"""Analytics: every user sees only their own company's numbers (Super Admin sees the platform)."""
from fastapi import APIRouter, Depends

from app.database_backend import get_connection
from app.dependencies import get_current_user

router = APIRouter()


@router.get("")
def analytics(user=Depends(get_current_user)):
    sa = user["is_superadmin"]
    org = user["organization_id"]

    def scoped(col="organization_id"):
        return ("1=1", []) if sa else (f"{col} = ?", [org])

    conn = get_connection()
    try:
        def one(sql, where_params):
            w, p = where_params
            return conn.execute(sql.format(w=w), p).fetchone()[0] or 0

        w = scoped()
        totals = {
            "campaigns": one("SELECT COUNT(*) FROM campaigns WHERE {w} AND channel IS NOT NULL", w),
            "contacts": one("SELECT COUNT(*) FROM leads WHERE {w}", w),
            "messages_sent": one("SELECT COUNT(*) FROM campaign_recipients WHERE {w} AND status='sent'", w),
            "messages_failed": one("SELECT COUNT(*) FROM campaign_recipients WHERE {w} AND status='failed'", w),
            "messages_not_sent": one("SELECT COUNT(*) FROM campaign_recipients WHERE {w} AND status='not_sent'", w),
            "ai_chats": one("SELECT COUNT(*) FROM chat_history WHERE {w}", w),
            "knowledge_items": one("SELECT COUNT(*) FROM kb_items WHERE " + ("1=1" if sa else "organization_id = ?"),
                                   ("1=1", []) if sa else ("", [org])),
        }
        wr = scoped()
        by_channel = [dict(r) for r in conn.execute(
            f"""SELECT channel, SUM(status='sent') AS sent, SUM(status='failed') AS failed,
                       SUM(status='not_sent') AS not_sent, COUNT(*) AS total
                FROM campaign_recipients WHERE {wr[0]} GROUP BY channel""", wr[1])]
        per_day = [dict(r) for r in conn.execute(
            f"""SELECT DATE(COALESCE(sent_at, created_at)) AS day, COUNT(*) AS messages
                FROM campaign_recipients
                WHERE {wr[0]} AND status IN ('sent','failed')
                  AND DATE(COALESCE(sent_at, created_at)) >= DATE('now','-13 days')
                GROUP BY day ORDER BY day""", wr[1])]
        wc = scoped("c.organization_id")
        recent = [dict(r) for r in conn.execute(
            f"""SELECT c.id, c.campaign_name, c.channel, c.status, c.total_recipients, c.created_at,
                       SUM(r.status='sent') AS sent, SUM(r.status='failed') AS failed
                FROM campaigns c LEFT JOIN campaign_recipients r ON r.campaign_id = c.id
                WHERE {wc[0]} AND c.channel IS NOT NULL
                GROUP BY c.id ORDER BY c.id DESC LIMIT 8""", wc[1])]
        attempted = totals["messages_sent"] + totals["messages_failed"]
        totals["delivery_rate"] = round(100 * totals["messages_sent"] / attempted, 1) if attempted else None
        return {"scope": "platform" if sa else "company", "user": user["name"],
                "totals": totals, "by_channel": by_channel, "per_day": per_day, "recent_campaigns": recent}
    finally:
        conn.close()
