# SkyModderAI / ModCheck — Windows PowerShell run script
# Run: .\run.ps1
# Requires Python 3.8+ (py launcher or python in PATH)

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

if (-not (Test-Path "venv")) {
    Write-Host "Creating virtual environment..."
    python -m venv venv
}

Write-Host "Installing dependencies..."
& .\venv\Scripts\pip install -q -r requirements.txt

if (-not (Test-Path "data\skyrimse_mod_database.json")) {
    Write-Host "Downloading LOOT masterlist (skyrimse)..."
    & .\venv\Scripts\python loot_parser.py skyrimse
}

Write-Host "Starting ModCheck on http://127.0.0.1:5000"
& .\venv\Scripts\python app.py
