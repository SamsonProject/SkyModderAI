#!/usr/bin/env bash
# ModCheck build script — run before deploy to pre-download LOOT data.
# Eliminates cold-start delay on first request (Render, etc.).
set -e
echo "ModCheck: Installing dependencies..."
pip install -r requirements.txt --quiet
echo "ModCheck: Pre-downloading LOOT masterlist (skyrimse)..."
python3 loot_parser.py skyrimse
echo "ModCheck: Build complete."
