from datetime import datetime, timedelta, timezone
import jwt
from jwt import InvalidTokenError
from fastapi import HTTPException, status
from app.config import JWT_SECRET_KEY, JWT_ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES

def create_access_token(user: dict) -> str:
    if not JWT_SECRET_KEY or JWT_SECRET_KEY == "REPLACE_WITH_A_LONG_RANDOM_SECRET":
        raise RuntimeError("Set JWT_SECRET_KEY in Backend_for_website/.env before login.")
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user["user_id"]),
        "email": user["email"],
        "organization_id": user.get("organization_id"),
        "roles": user.get("role", []),
        "permissions": user.get("permissions", []),
        "is_superadmin": bool(user.get("is_superadmin")),
        "iat": now,
        "exp": now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    }
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)

def decode_access_token(token: str) -> dict:
    if not JWT_SECRET_KEY or JWT_SECRET_KEY == "REPLACE_WITH_A_LONG_RANDOM_SECRET":
        raise HTTPException(status_code=500, detail="JWT secret is not configured.")
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        if not payload.get("sub"):
            raise InvalidTokenError("Missing subject")
        return payload
    except InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired access token.",
            headers={"WWW-Authenticate": "Bearer"},
        )
