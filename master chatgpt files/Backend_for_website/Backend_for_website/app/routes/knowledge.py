"""Knowledge base: upload files and/or write notes; the AI re-learns the company's knowledge.

Each company has its own knowledge base. The Super Admin account manages the platform
(global) knowledge base. "Training" here means re-indexing: every file and note is split
into chunks and embedded, then retrieved when the AI answers or writes campaigns.
"""
import re
import sys
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from fastapi.concurrency import run_in_threadpool

from app.config import MOSETA_AI_DIR
from app.database_backend import get_connection
from app.dependencies import require_permission

if str(MOSETA_AI_DIR) not in sys.path:
    sys.path.insert(0, str(MOSETA_AI_DIR))

router = APIRouter()

ALLOWED_EXT = {".pdf", ".txt", ".md", ".csv"}
MAX_FILE_BYTES = 10 * 1024 * 1024
MAX_FILES = 10
MAX_NOTE_CHARS = 20000
UPLOAD_ROOT = MOSETA_AI_DIR / "uploads"
GLOBAL_DOCS = MOSETA_AI_DIR / "product_docs"

kb_permission = require_permission("documents.manage")


def _scope(user):
    return None if user["is_superadmin"] else user["organization_id"]


def _upload_dir(org_id):
    d = GLOBAL_DOCS if org_id is None else UPLOAD_ROOT / f"org_{int(org_id)}"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _where(org_id):
    return ("organization_id IS NULL", []) if org_id is None else ("organization_id = ?", [org_id])


def _engine():
    try:
        import rag_engine
        return rag_engine
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"AI engine unavailable: {exc}")


def _retrain(org_id):
    """Rebuild this scope's index from every registered file and note."""
    eng = _engine()
    conn = get_connection()
    try:
        clause, params = _where(org_id)
        rows = conn.execute(
            f"SELECT kind, title, file_path, content FROM kb_items WHERE {clause} ORDER BY id", params
        ).fetchall()
    finally:
        conn.close()
    items = [{"source": r["title"], "path": r["file_path"] if r["kind"] == "file" else None,
              "text": r["content"]} for r in rows]
    return eng.rebuild_index(org_id, items)


def _list(org_id):
    conn = get_connection()
    try:
        clause, params = _where(org_id)
        rows = conn.execute(
            f"SELECT id, kind, title, content, size_bytes, created_at FROM kb_items "
            f"WHERE {clause} ORDER BY id DESC", params).fetchall()
        return [{"id": r["id"], "kind": r["kind"], "title": r["title"],
                 "preview": (r["content"] or "")[:200], "size_bytes": r["size_bytes"],
                 "created_at": r["created_at"]} for r in rows]
    finally:
        conn.close()


@router.get("")
def list_items(user=Depends(kb_permission)):
    org_id = _scope(user)
    eng = _engine()
    info = eng.kb_info(org_id) if eng.is_ready() else None
    items = _list(org_id)
    return {
        "scope": "platform" if org_id is None else "company",
        "items": items,
        "chunks": info["chunks"] if info else None,
        # A company with no documents of its own is answered from Moseta's original base knowledge.
        "using_base": org_id is not None and len(items) == 0,
    }


@router.get("/{item_id}/file")
def view_file(item_id: int, user=Depends(kb_permission)):
    """Open an uploaded file (PDF/text) in the browser. Only the owner's files are reachable."""
    org_id = _scope(user)
    conn = get_connection()
    try:
        clause, params = _where(org_id)
        row = conn.execute(f"SELECT kind, title, file_path FROM kb_items WHERE id = ? AND {clause}",
                           [item_id] + params).fetchone()
    finally:
        conn.close()
    if row is None or row["kind"] != "file" or not row["file_path"]:
        raise HTTPException(status_code=404, detail="File not found.")
    p = Path(row["file_path"]).resolve()
    if not any(str(p).startswith(str(a.resolve())) for a in (UPLOAD_ROOT, GLOBAL_DOCS)) or not p.exists():
        raise HTTPException(status_code=404, detail="File not found.")
    media = {".pdf": "application/pdf", ".txt": "text/plain", ".md": "text/plain", ".csv": "text/plain"}
    return FileResponse(p, media_type=media.get(p.suffix.lower(), "application/octet-stream"),
                        filename=row["title"], content_disposition_type="inline")


@router.post("")
async def add_items(
    files: list[UploadFile] = File(default=[]),
    note_title: str = Form(default=""),
    note_text: str = Form(default=""),
    user=Depends(kb_permission),
):
    org_id = _scope(user)
    note_text = note_text.strip()
    files = [f for f in files if f.filename]
    if not files and not note_text:
        raise HTTPException(status_code=400, detail="Attach at least one file or write some information.")
    if len(files) > MAX_FILES:
        raise HTTPException(status_code=400, detail=f"Upload at most {MAX_FILES} files at a time.")
    if len(note_text) > MAX_NOTE_CHARS:
        raise HTTPException(status_code=400, detail=f"Notes are limited to {MAX_NOTE_CHARS} characters.")

    # Validate everything before saving anything.
    staged = []
    for f in files:
        name = Path(f.filename).name
        ext = Path(name).suffix.lower()
        if ext not in ALLOWED_EXT:
            raise HTTPException(status_code=400,
                                detail=f"'{name}': unsupported type. Allowed: PDF, TXT, MD, CSV.")
        data = await f.read(MAX_FILE_BYTES + 1)
        if len(data) > MAX_FILE_BYTES:
            raise HTTPException(status_code=400, detail=f"'{name}' is larger than 10 MB.")
        if not data:
            raise HTTPException(status_code=400, detail=f"'{name}' is empty.")
        if ext == ".pdf" and not data.startswith(b"%PDF"):
            raise HTTPException(status_code=400, detail=f"'{name}' is not a valid PDF.")
        staged.append((name, data))

    saved_paths, conn = [], get_connection()
    try:
        folder = _upload_dir(org_id)
        for name, data in staged:
            safe = re.sub(r"[^A-Za-z0-9._-]", "_", name)
            path = folder / f"{uuid.uuid4().hex[:8]}_{safe}"
            path.write_bytes(data)
            saved_paths.append(path)
            conn.execute(
                "INSERT INTO kb_items (organization_id, kind, title, file_path, size_bytes, created_by) "
                "VALUES (?,?,?,?,?,?)", (org_id, "file", name, str(path), len(data), user["user_id"]))
        if note_text:
            conn.execute(
                "INSERT INTO kb_items (organization_id, kind, title, content, size_bytes, created_by) "
                "VALUES (?,?,?,?,?,?)",
                (org_id, "note", (note_title.strip() or "Note")[:120], note_text,
                 len(note_text.encode()), user["user_id"]))
        conn.commit()
    except Exception:
        conn.rollback()
        for p in saved_paths:
            p.unlink(missing_ok=True)
        raise HTTPException(status_code=500, detail="Could not save the uploaded information.")
    finally:
        conn.close()

    chunks, problems = await run_in_threadpool(_retrain, org_id)
    return {"added_files": len(staged), "added_note": bool(note_text),
            "chunks": chunks, "warnings": problems,
            "message": "Knowledge updated. The AI will now use this information."}


@router.delete("/{item_id}")
async def delete_item(item_id: int, user=Depends(kb_permission)):
    org_id = _scope(user)
    conn = get_connection()
    try:
        clause, params = _where(org_id)
        row = conn.execute(f"SELECT id, kind, file_path FROM kb_items WHERE id = ? AND {clause}",
                           [item_id] + params).fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="Item not found.")
        conn.execute("DELETE FROM kb_items WHERE id = ?", (item_id,))
        conn.commit()
    finally:
        conn.close()
    if row["kind"] == "file" and row["file_path"]:
        p = Path(row["file_path"]).resolve()
        allowed = [UPLOAD_ROOT.resolve(), GLOBAL_DOCS.resolve()]
        if any(str(p).startswith(str(a)) for a in allowed):
            p.unlink(missing_ok=True)
    chunks, problems = await run_in_threadpool(_retrain, org_id)
    return {"deleted": True, "chunks": chunks, "warnings": problems}
