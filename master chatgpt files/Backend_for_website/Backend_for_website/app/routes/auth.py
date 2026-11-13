import sys
from app.config import PROJECT_ROOT, ACCESS_TOKEN_EXPIRE_MINUTES
from fastapi import APIRouter, Depends, HTTPException
from app.schemas.auth import LoginRequest, SignupRequest
from app.database_backend import get_connection
from app.security import create_access_token
from app.dependencies import get_current_user

# Reuse the existing authentication and RBAC implementation.
DB_SERVICE_DIR = PROJECT_ROOT / "moseta_db"
if str(DB_SERVICE_DIR) not in sys.path:
    sys.path.insert(0, str(DB_SERVICE_DIR))

try:
    from auth_service import authenticate_user, hash_password
except Exception as exc:
    authenticate_user = None
    hash_password = None
    AUTH_IMPORT_ERROR = str(exc)
else:
    AUTH_IMPORT_ERROR = None

router = APIRouter()

@router.post("/login")
def login(payload: LoginRequest):
    if authenticate_user is None:
        raise HTTPException(
            status_code=500,
            detail=f"Could not import moseta_db/auth_service.py: {AUTH_IMPORT_ERROR}",
        )
    try:
        user = authenticate_user(str(payload.email), payload.password)
    except ValueError as exc:
        raise HTTPException(status_code=401, detail=str(exc))
    except Exception:
        raise HTTPException(status_code=500, detail="Authentication service error.")

    token = create_access_token(user)
    safe_user = {
        "user_id": user["user_id"],
        "name": user["name"],
        "email": user["email"],
        "organization_id": user.get("organization_id"),
        "role": user.get("role", []),
        "permissions": user.get("permissions", []),
        "is_superadmin": bool(user.get("is_superadmin")),
    }
    return {
        "access_token": token,
        "token_type": "bearer",
        "expires_in_minutes": ACCESS_TOKEN_EXPIRE_MINUTES,
        "user": safe_user,
    }

@router.get("/me")
def me(user=Depends(get_current_user)):
    return user


@router.post("/signup", status_code=201)
def signup(payload: SignupRequest):
    """Public self-service signup for a company user.

    Creates the user plus their own organization and assigns the `company_admin`
    role, all in one transaction. Passwords are stored only as PBKDF2 hashes.
    """
    if hash_password is None:
        raise HTTPException(status_code=500, detail="Authentication service unavailable.")
    name = " ".join(payload.name.split())
    email = str(payload.email).strip().lower()

    conn = get_connection()
    try:
        if conn.execute("SELECT 1 FROM users WHERE LOWER(email) = ?", (email,)).fetchone():
            raise HTTPException(status_code=409, detail="An account with this email already exists.")
        role = conn.execute(
            "SELECT id FROM roles WHERE role_name = 'company_admin' AND scope = 'organization' "
            "AND organization_id IS NULL"
        ).fetchone()
        if role is None:
            raise HTTPException(status_code=500, detail="company_admin role is not configured.")

        org_id = conn.execute(
            "INSERT INTO organizations (company_name, company_email, status) VALUES (?,?, 'active')",
            (f"{name}'s Company", email),
        ).lastrowid
        user_id = conn.execute(
            "INSERT INTO users (organization_id, full_name, email, password_hash, "
            "is_platform_superadmin, status) VALUES (?,?,?,?,0,'active')",
            (org_id, name, email, hash_password(payload.password)),
        ).lastrowid
        conn.execute("INSERT INTO user_roles (user_id, role_id) VALUES (?,?)", (user_id, role["id"]))
        conn.execute(
            "INSERT INTO audit_logs (organization_id, user_id, action, entity_type, entity_id) "
            "VALUES (?,?,?,?,?)",
            (org_id, user_id, "user_signup", "users", user_id),
        )
        conn.commit()
    except HTTPException:
        conn.rollback()
        raise
    except Exception:
        conn.rollback()
        raise HTTPException(status_code=500, detail="Could not create account.")
    finally:
        conn.close()
    return {"created": True, "user_id": user_id, "name": name, "email": email}
