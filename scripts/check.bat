@echo off
cd /d "%~dp0.."
python -m app.tools check
echo.
pause
