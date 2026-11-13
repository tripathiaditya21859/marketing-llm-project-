@echo off
cd /d "%~dp0master chatgpt files\Backend_for_website\Backend_for_website"
"%~dp0Moseta_AI\.venv\Scripts\python.exe" -m uvicorn app.main:app --host 127.0.0.1 --port 8000
