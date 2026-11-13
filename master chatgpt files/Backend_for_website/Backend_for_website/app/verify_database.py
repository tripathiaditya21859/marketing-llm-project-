from app.config import (
    APP_DIR,
    BACKEND_DIR,
    PROJECT_ROOT,
    DATABASE_PATH
)

print("\n========== MOSETA DATABASE PATH CHECK ==========")

print("APP DIRECTORY:", APP_DIR)
print("BACKEND DIRECTORY:", BACKEND_DIR)
print("PROJECT ROOT:", PROJECT_ROOT)

print("\nDATABASE PATH:", DATABASE_PATH)

print("DATABASE EXISTS:", DATABASE_PATH.exists())
print("DATABASE FOLDER EXISTS:", DATABASE_PATH.parent.exists())

print("\n===============================================")

