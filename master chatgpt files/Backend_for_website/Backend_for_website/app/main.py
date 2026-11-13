
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import FRONTEND_ORIGINS, DATABASE_PATH
from app.routes import auth, health, resources, chat, knowledge, campaigns, leads, analytics, admin


# Initialize FastAPI
app = FastAPI(
    title="Moseta AI API",
    description="Multi-tenant backend for Moseta AI",
    version="1.0.0",
)


from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=FRONTEND_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



# Register API Routers
app.include_router(
    health.router,
    tags=["Health"]
)

app.include_router(
    auth.router,
    prefix="/api/auth",
    tags=["Authentication"]
)

app.include_router(
    resources.router,
    prefix="/api/resources",
    tags=["Business Resources"]
)


app.include_router(
    chat.router,
    prefix="/api/chat",
    tags=["AI Chat"]
)


for _router, _prefix, _tag in (
    (knowledge.router, "/api/knowledge", "Knowledge Base"),
    (campaigns.router, "/api/campaigns", "Campaigns"),
    (leads.router, "/api/leads", "Leads & Customers"),
    (analytics.router, "/api/analytics", "Analytics"),
    (admin.router, "/api/admin", "Super Admin"),
):
    app.include_router(_router, prefix=_prefix, tags=[_tag])


@app.on_event("startup")
def _init_storage():
    from app.db_setup import ensure_schema
    ensure_schema()

    def _warm_up():  # load the AI model in the background so the first chat is fast
        try:
            from app.routes.chat import _engine
            _engine().load()
        except Exception as exc:
            print("AI warm-up skipped:", exc)

    import threading
    threading.Thread(target=_warm_up, daemon=True).start()


# Root Endpoint
@app.get("/", tags=["Root"])
def root():
    return {
        "name": "Moseta AI API",
        "status": "running",
        "docs": "/docs",
        "database_file": DATABASE_PATH.name,
    }

