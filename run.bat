@echo off
REM SkyModderAI — Windows CMD run script
REM Run from project root. Requires Python 3.8+ on PATH.

cd /d "%~dp0"

if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

echo Installing dependencies...
venv\Scripts\pip install -q -r requirements.txt

if not exist "data\skyrimse_mod_database.json" (
    echo Downloading LOOT masterlist (skyrimse)...
    venv\Scripts\python loot_parser.py skyrimse
)

echo Starting SkyModderAI on http://127.0.0.1:5000
venv\Scripts\python app.py
