@echo off
start "Moseta Backend" "%~dp0start_backend.bat"
start "Moseta Frontend" "%~dp0start_frontend.bat"
echo Backend: http://127.0.0.1:8000/docs   Frontend: http://127.0.0.1:5173
