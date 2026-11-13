from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from app.security import decode_access_token
from app.database_backend import get_connection

bearer_scheme = HTTPBearer(auto_error=False)

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
):
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = decode_access_token(credentials.credentials)
    try:
        user_id = int(payload["sub"])
    except (ValueError, TypeError, KeyError):
        raise HTTPException(status_code=401, detail="Invalid token subject.")

    conn = get_connection()
    try:
        row = conn.execute(
            """
            SELECT id, organization_id, full_name, email,
                   is_platform_superadmin, status
            FROM users WHERE id = ?
            """,
            (user_id,),
        ).fetchone()

        if row is None or str(row["status"]).lower() != "active":
            raise HTTPException(status_code=401, detail="User account is inactive.")
        # The token must belong to this exact account (guards against reused or renumbered ids).
        if str(payload.get("email", "")).lower() != str(row["email"]).lower():
            raise HTTPException(status_code=401, detail="Session is no longer valid. Please sign in again.")

        org_id = row["organization_id"]
        is_superadmin = bool(row["is_platform_superadmin"])
        if not is_superadmin:
            if org_id is None:
                raise HTTPException(status_code=403, detail="User has no organization.")
            org = conn.execute(
                "SELECT status FROM organizations WHERE id = ?", (org_id,)
            ).fetchone()
            if org is None or str(org["status"]).lower() not in ("active", "approved"):
                raise HTTPException(status_code=403, detail="Organization is not active.")

        return {
            "user_id": row["id"],
            "organization_id": org_id,
            "name": row["full_name"],
            "email": row["email"],
            "is_superadmin": is_superadmin,
            "roles": payload.get("roles", []),
            "permissions": payload.get("permissions", []),
            "authenticated": True,
        }
    finally:
        conn.close()

def require_permission(permission_key: str):
    def checker(user=Depends(get_current_user)):
        if user["is_superadmin"] or permission_key in user["permissions"]:
            return user
        raise HTTPException(status_code=403, detail="Permission denied.")
    return checker
