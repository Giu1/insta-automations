@echo off
cd /d "%~dp0.."
echo Starting Insta Automations on http://127.0.0.1:8080  (close this window to stop)
python -m uvicorn app.main:app --host 127.0.0.1 --port 8080
pause
