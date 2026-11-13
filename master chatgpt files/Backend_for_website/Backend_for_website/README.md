# Moseta AI Backend

FastAPI starter connected to the existing SQLite database:
`Master_Folder_Moseta_AI/moseta_db/moseta.db`.

## Place this folder
Extract `Backend_for_website` inside `Master_Folder_Moseta_AI`, beside
`moseta_db`, `Moseta_AI`, and `frontend_for_website`.

## Activate the virtual environment
From the master folder in PowerShell:

```powershell
.\venv\Scripts\Activate.ps1
```

## Install dependencies
```powershell
cd Backend_for_website
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## Set a JWT secret
Generate one:
```powershell
python -c "import secrets; print(secrets.token_urlsafe(48))"
```
Put the result in `.env` as `JWT_SECRET_KEY`. Do not share or commit `.env`.

## Verify DATABASE_PATH
The default assumes:
```text
Master_Folder_Moseta_AI/
  Backend_for_website/
  moseta_db/moseta.db
```
Update `.env` if your database is elsewhere. The relative path is resolved
from the `Backend_for_website` folder.

## Run
From inside `Backend_for_website`:
```powershell
python -m uvicorn app.main:app --reload
```
Open http://127.0.0.1:8000/docs and http://127.0.0.1:8000/health.

## Login
POST `/api/auth/login`:
```json
{
  "email": "your-admin-email",
  "password": "your-password"
}
```
The endpoint calls the existing `moseta_db/auth_service.py`. Use the returned
access token in Swagger's Authorize dialog as `Bearer YOUR_TOKEN`.

## Resource endpoints
Examples:
- GET `/api/resources/products`
- GET `/api/resources/leads`
- GET `/api/resources/customer_queries`
- GET `/api/resources/documents`
- GET `/api/resources/campaigns`
- GET `/api/resources/price_lists`

The resource layer introspects the real SQLite table columns. Company users
are denied access to tables without an `organization_id` column. This is
intentional: it fails closed instead of risking cross-company data exposure.

## Before production
This is a development foundation, not a finished production security review.
Add token revocation/refresh, rate limiting, password reset, email verification,
upload validation and private file storage, audit event writing, and tested
business workflows. Back up the database before schema changes. Do not expose
the development server directly to the public internet.
