"""AI chat endpoint: authenticated users talk to the local Moseta LLM (RAG over PDFs).

Every exchange is stored in `chat_history`; generated campaign drafts are also saved
to the existing `campaigns` table (status 'draft') for the user's organization, and an
`audit_logs` row is written.
"""
import json
import sys
from fastapi import APIRouter, Depends, HTTPException
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel, Field

from app.config import MOSETA_AI_DIR
from app.database_backend import get_connection
from app.dependencies import get_current_user

router = APIRouter()

if str(MOSETA_AI_DIR) not in sys.path:
    sys.path.insert(0, str(MOSETA_AI_DIR))


class Turn(BaseModel):
    question: str = Field(max_length=2000)
    answer: str = Field(max_length=6000)


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)
    history: list[Turn] = Field(default_factory=list, max_length=6)  # recent conversation, oldest first


def ensure_chat_table():
    conn = get_connection()
    try:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS chat_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                organization_id INTEGER,
                user_id INTEGER NOT NULL,
                question TEXT NOT NULL,
                answer TEXT NOT NULL,
                is_campaign INTEGER DEFAULT 0,
                platforms TEXT,
                sources TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (organization_id) REFERENCES organizations(id),
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
            """
        )
        conn.commit()
    finally:
        conn.close()


def _engine():
    try:
        import rag_engine
        return rag_engine
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"AI engine unavailable: {exc}")


@router.get("/status")
def status(user=Depends(get_current_user)):
    eng = _engine()
    return {"model_loaded": eng.is_ready(), "model": "Qwen2.5-0.5B-Instruct"}


@router.post("")
async def chat(payload: ChatRequest, user=Depends(get_current_user)):
    eng = _engine()
    question = payload.message.strip()
    try:
        answer, results, is_campaign, platforms = await run_in_threadpool(
            eng.generate_answer, question, None,
            None if user["is_superadmin"] else user["organization_id"],
            [(t.question, t.answer) for t in payload.history],
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"AI generation failed: {exc}")

    sources = [
        {"source": r["source"], "chunk": r["chunk_number"], "score": round(r["score"], 4)}
        for r in results
    ]

    conn = get_connection()
    try:
        cur = conn.execute(
            "INSERT INTO chat_history (organization_id, user_id, question, answer, "
            "is_campaign, platforms, sources) VALUES (?,?,?,?,?,?,?)",
            (user["organization_id"], user["user_id"], question, answer,
             int(is_campaign), ", ".join(platforms), json.dumps(sources)),
        )
        chat_id = cur.lastrowid
        campaign_id = None
        if is_campaign and user["organization_id"] is not None:
            c = conn.execute(
                "INSERT INTO campaigns (organization_id, campaign_name, platform, status) "
                "VALUES (?,?,?,'draft')",
                (user["organization_id"], question[:80], ", ".join(platforms)),
            )
            campaign_id = c.lastrowid
        conn.execute(
            "INSERT INTO audit_logs (organization_id, user_id, action, entity_type, entity_id) "
            "VALUES (?,?,?,?,?)",
            (user["organization_id"], user["user_id"],
             "ai_campaign_generated" if is_campaign else "ai_chat", "chat_history", chat_id),
        )
        conn.commit()
    finally:
        conn.close()

    return {
        "id": chat_id,
        "answer": answer,
        "is_campaign": is_campaign,
        "platforms": platforms,
        "sources": sources,
        "campaign_id": campaign_id,
    }


@router.get("/history")
def history(limit: int = 50, user=Depends(get_current_user)):
    limit = max(1, min(limit, 200))
    conn = get_connection()
    try:
        sql = ("SELECT id, question, answer, is_campaign, platforms, sources, created_at "
               "FROM chat_history WHERE user_id = ? ORDER BY id DESC LIMIT ?")
        rows = conn.execute(sql, (user["user_id"], limit)).fetchall()
        return {"items": [dict(r) for r in rows][::-1]}
    finally:
        conn.close()
