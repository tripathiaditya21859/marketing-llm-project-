# Moseta AI Frontend

React + Vite starter.

## Run
Open a terminal in this folder and run:
```powershell
npm install
```
Copy `.env.example` to `.env`, confirm the endpoint paths match your FastAPI `/docs`, then:
```powershell
npm run dev
```
Open http://127.0.0.1:5173.

Keep the FastAPI backend running separately on http://127.0.0.1:8000.

The login path is prefilled from the Swagger screenshot you shared. The form sends `{ "email": "...", "password": "..." }`.
The frontend route guard is only a user-experience feature. Enforce RBAC on every protected backend endpoint.
