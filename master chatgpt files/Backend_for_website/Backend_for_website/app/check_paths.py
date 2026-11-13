
import os
from pathlib import Path
from app.config import (
    APP_DIR,
    BACKEND_DIR,
    PROJECT_ROOT,
    DATABASE_PATH
)

print("\n========== MOSETA PATH DIAGNOSTICS ==========")

print("APP DIR:", APP_DIR)
print("BACKEND DIR:", BACKEND_DIR)
print("PROJECT ROOT:", PROJECT_ROOT)

print("\nENV DATABASE PATH:", os.getenv("DATABASE_PATH"))
print("RESOLVED DATABASE:", DATABASE_PATH)
print("DATABASE EXISTS:", DATABASE_PATH.exists())

print("\nChecking database folder:")

db_folder = PROJECT_ROOT / "moseta_db"

print("Database folder:", db_folder)
print("Folder exists:", db_folder.exists())

if db_folder.exists():
    print("\nFiles inside database folder:")
    for file in db_folder.iterdir():
        print(file.name)

print("\n============================================")
