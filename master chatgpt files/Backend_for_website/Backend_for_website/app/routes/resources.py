from typing import Any
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from app.database_backend import get_connection
from app.dependencies import get_current_user

router = APIRouter()

# Allowlist: these table names are present in the database inspection screenshot.
RESOURCE_PERMISSIONS = {
    "organizations": "organizations.manage",
    "users": "users.manage",
    "leads": "leads.manage",
    "customer_queries": "queries.manage",
    "products": "products.manage",
    "price_lists": "pricing.manage",
    "documents": "documents.manage",
    "campaigns": "campaigns.manage",
    "audit_logs": "audit.view",
}
SENSITIVE_COLUMNS = {"password_hash", "password", "token", "secret", "reset_token"}

class ResourcePayload(BaseModel):
    data: dict[str, Any]

def _table_columns(conn, table):
    rows = conn.execute(f'PRAGMA table_info("{table}")').fetchall()
    if not rows:
        raise HTTPException(status_code=404, detail="Resource table not found.")
    return {row["name"] for row in rows}

def _primary_key(conn, table):
    rows = conn.execute(f'PRAGMA table_info("{table}")').fetchall()
    for row in rows:
        if row["pk"]:
            return row["name"]
    raise HTTPException(status_code=500, detail="Resource has no primary key.")

def _validate_access(resource, user):
    if resource not in RESOURCE_PERMISSIONS:
        raise HTTPException(status_code=404, detail="Unknown resource.")
    if resource in ("organizations", "users") and not user["is_superadmin"]:
        raise HTTPException(status_code=403, detail="Only Super Admin can access this resource.")
    permission = RESOURCE_PERMISSIONS[resource]
    if not user["is_superadmin"] and permission not in user["permissions"]:
        raise HTTPException(status_code=403, detail="Permission denied.")

def _check_tenant_scope(columns, user):
    if not user["is_superadmin"] and "organization_id" not in columns:
        raise HTTPException(
            status_code=403,
            detail="Organization-scoped access is disabled: this table has no organization_id column."
        )

def _safe_row(row):
    result = dict(row)
    for key in list(result):
        if key.lower() in SENSITIVE_COLUMNS:
            result.pop(key, None)
    return result

@router.get("/{resource}")
def list_resources(
    resource: str,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    user=Depends(get_current_user),
):
    _validate_access(resource, user)
    conn = get_connection()
    try:
        columns = _table_columns(conn, resource)
        _check_tenant_scope(columns, user)
        sql = f'SELECT * FROM "{resource}"'
        params = []
        if not user["is_superadmin"]:
            sql += ' WHERE organization_id = ?'
            params.append(user["organization_id"])
        sql += " LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        rows = conn.execute(sql, params).fetchall()
        return {"items": [_safe_row(row) for row in rows], "limit": limit, "offset": offset}
    finally:
        conn.close()

@router.get("/{resource}/{record_id}")
def get_resource(resource: str, record_id: int, user=Depends(get_current_user)):
    _validate_access(resource, user)
    conn = get_connection()
    try:
        columns = _table_columns(conn, resource)
        _check_tenant_scope(columns, user)
        pk = _primary_key(conn, resource)
        sql = f'SELECT * FROM "{resource}" WHERE "{pk}" = ?'
        params = [record_id]
        if not user["is_superadmin"]:
            sql += " AND organization_id = ?"
            params.append(user["organization_id"])
        row = conn.execute(sql, params).fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="Record not found.")
        return _safe_row(row)
    finally:
        conn.close()

@router.post("/{resource}")
def create_resource(resource: str, payload: ResourcePayload, user=Depends(get_current_user)):
    _validate_access(resource, user)
    conn = get_connection()
    try:
        columns = _table_columns(conn, resource)
        _check_tenant_scope(columns, user)
        data = dict(payload.data)
        if any(key.lower() in SENSITIVE_COLUMNS or key.lower() == "id" for key in data):
            raise HTTPException(status_code=400, detail="Sensitive/generated fields cannot be supplied.")
        unknown = set(data) - columns
        if unknown:
            raise HTTPException(status_code=400, detail=f"Unknown fields: {', '.join(sorted(unknown))}")
        if not user["is_superadmin"]:
            data["organization_id"] = user["organization_id"]
        if not data:
            raise HTTPException(status_code=400, detail="No data supplied.")
        names = list(data)
        cols_sql = ", ".join(f'"{name}"' for name in names)
        marks = ", ".join("?" for _ in names)
        cursor = conn.execute(
            f'INSERT INTO "{resource}" ({cols_sql}) VALUES ({marks})',
            [data[name] for name in names],
        )
        conn.commit()
        return {"created": True, "id": cursor.lastrowid}
    except HTTPException:
        raise
    except Exception as exc:
        conn.rollback()
        raise HTTPException(status_code=400, detail=f"Could not create record: {exc}")
    finally:
        conn.close()

@router.patch("/{resource}/{record_id}")
def update_resource(
    resource: str,
    record_id: int,
    payload: ResourcePayload,
    user=Depends(get_current_user),
):
    _validate_access(resource, user)
    conn = get_connection()
    try:
        columns = _table_columns(conn, resource)
        _check_tenant_scope(columns, user)
        pk = _primary_key(conn, resource)
        data = dict(payload.data)
        protected = SENSITIVE_COLUMNS | {"id", pk.lower(), "organization_id"}
        if any(key.lower() in protected for key in data):
            raise HTTPException(status_code=400, detail="Protected fields cannot be updated.")
        unknown = set(data) - columns
        if unknown:
            raise HTTPException(status_code=400, detail=f"Unknown fields: {', '.join(sorted(unknown))}")
        if not data:
            raise HTTPException(status_code=400, detail="No update fields supplied.")
        assignments = ", ".join(f'"{key}" = ?' for key in data)
        sql = f'UPDATE "{resource}" SET {assignments} WHERE "{pk}" = ?'
        params = list(data.values()) + [record_id]
        if not user["is_superadmin"]:
            sql += " AND organization_id = ?"
            params.append(user["organization_id"])
        cursor = conn.execute(sql, params)
        conn.commit()
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Record not found.")
        return {"updated": True, "id": record_id}
    except HTTPException:
        raise
    except Exception as exc:
        conn.rollback()
        raise HTTPException(status_code=400, detail=f"Could not update record: {exc}")
    finally:
        conn.close()
