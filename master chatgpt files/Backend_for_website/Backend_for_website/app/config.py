from pathlib import Path
import os
from dotenv import load_dotenv

# Current application directory
APP_DIR = Path(__file__).resolve().parent

# Backend directory
BACKEND_DIR = APP_DIR.parent

# Actual project root:
# Master_Folder_Moseta_AI
PROJECT_ROOT = Path(__file__).resolve().parents[3]

# Load environment variables
load_dotenv(BACKEND_DIR / ".env")

# SQLite database location
DATABASE_PATH = (
    PROJECT_ROOT / "moseta_db" / "moseta.db"
).resolve()

# Local LLM (Qwen2.5-0.5B + PDF knowledge base) folder
MOSETA_AI_DIR = (PROJECT_ROOT.parent / "Moseta_AI").resolve()

# JWT settings
JWT_SECRET_KEY = os.getenv(
    "JWT_SECRET_KEY",
    "change-this-secret-before-production"
)

JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")

ACCESS_TOKEN_EXPIRE_MINUTES = int(
    os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60")
)

# Frontend CORS settings
FRONTEND_ORIGINS = [
    item.strip()
    for item in os.getenv(
        "FRONTEND_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173"
    ).split(",")
    if item.strip()
]