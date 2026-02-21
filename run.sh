#!/usr/bin/env bash
# SkyModderAI — Run locally (Linux, macOS, WSL)
# Usage: ./run.sh
set -e
cd "$(dirname "$0")"

# Prefer python3, fallback to python
PYTHON="${PYTHON:-$(command -v python3 2>/dev/null || command -v python)}"
if [ -z "$PYTHON" ]; then
    echo "Error: Python 3.11+ required. Install python3 or set PYTHON."
    exit 1
fi

if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    "$PYTHON" -m venv venv
fi

echo "Installing dependencies..."
./venv/bin/pip install -q -r requirements.txt

if [ ! -f "data/skyrimse_mod_database.json" ]; then
    echo "Downloading LOOT masterlist (skyrimse)..."
    ./venv/bin/python loot_parser.py skyrimse
fi

echo "Starting SkyModderAI on http://127.0.0.1:5000"
./venv/bin/python app.py
