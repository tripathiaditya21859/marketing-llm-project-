"""Start the whole Moseta AI website with one command:

    python run_moseta.py

Starts the backend (FastAPI + login + database + local Qwen LLM) and the frontend
(React/Vite), waits until both are ready, then opens the site in your browser.
Press Ctrl+C to stop everything.
"""
import os
import shutil
import subprocess
import sys
import time
import urllib.request
import webbrowser
from pathlib import Path

ROOT = Path(__file__).resolve().parent
AI_DIR = ROOT / "Moseta_AI"                      # LLM + PDF knowledge base (+ .venv)
BACKEND_DIR = ROOT / "master chatgpt files" / "Backend_for_website" / "Backend_for_website"
FRONTEND_DIR = ROOT / "master chatgpt files" / "frontend_for_website"
DB_FILE = ROOT / "master chatgpt files" / "moseta_db" / "moseta.db"

PY = AI_DIR / ".venv" / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
BACKEND_URL = "http://127.0.0.1:8000"
FRONTEND_URL = "http://127.0.0.1:5173"


def check():
    problems = []
    if not PY.exists():
        problems.append(f"Python environment not found: {PY}")
    if not (BACKEND_DIR / "app" / "main.py").exists():
        problems.append(f"Backend not found: {BACKEND_DIR}")
    if not (FRONTEND_DIR / "package.json").exists():
        problems.append(f"Frontend not found: {FRONTEND_DIR}")
    if not DB_FILE.exists():
        problems.append(f"Database not found: {DB_FILE}")
    if not (AI_DIR / "knowledge_base" / "embeddings.npy").exists():
        problems.append("Knowledge base missing - run: Moseta_AI/.venv/Scripts/python.exe Moseta_AI/ingest_documents.py")
    if shutil.which("npm") is None:
        problems.append("npm (Node.js) is not installed or not on PATH.")
    if problems:
        print("\nCannot start:\n - " + "\n - ".join(problems))
        sys.exit(1)


def wait_for(url, name, timeout=120):
    end = time.time() + timeout
    while time.time() < end:
        try:
            urllib.request.urlopen(url, timeout=2)
            print(f"  {name} ready: {url}")
            return True
        except Exception:
            time.sleep(1)
    print(f"  {name} did not start within {timeout}s")
    return False


def main():
    sys.stdout.reconfigure(line_buffering=True)
    check()
    if not (FRONTEND_DIR / "node_modules").exists():
        print("Installing frontend packages (first run only)...")
        subprocess.check_call([shutil.which("npm"), "install"], cwd=FRONTEND_DIR)

    print("Starting backend (API + database + AI model)...")
    backend = subprocess.Popen(
        [str(PY), "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8000"],
        cwd=BACKEND_DIR,
    )
    print("Starting frontend...")
    frontend = subprocess.Popen(
        [shutil.which("npm"), "run", "dev", "--", "--host", "127.0.0.1", "--port", "5173"],
        cwd=FRONTEND_DIR,
    )

    try:
        ok = wait_for(BACKEND_URL + "/health", "Backend") and wait_for(FRONTEND_URL, "Frontend")
        if ok:
            print(f"\nMoseta AI is running -> {FRONTEND_URL}")
            print("(The AI model loads on the first chat message, so the first reply is slow.)")
            print("Press Ctrl+C to stop.\n")
            webbrowser.open(FRONTEND_URL)
        while ok and backend.poll() is None and frontend.poll() is None:
            time.sleep(1)
        if ok:
            print("A server stopped unexpectedly.")
    except KeyboardInterrupt:
        pass
    finally:
        print("\nStopping Moseta AI...")
        for proc in (frontend, backend):
            if proc.poll() is None:
                if os.name == "nt":  # also stops child processes (npm -> node)
                    subprocess.run(["taskkill", "/F", "/T", "/PID", str(proc.pid)],
                                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                else:
                    proc.terminate()


if __name__ == "__main__":
    main()
##cd "C:\Users\Aditya\OneDrive\Desktop\scratch LLM\Master_Folder_Moseta_AI"