#!/usr/bin/env bash
# SkyModderAI build script — run before deploy to pre-download LOOT data.
# Eliminates cold-start delay on first request (Render, etc.).
set -e
echo "SkyModderAI: Installing dependencies..."
pip install -r requirements.txt --quiet
echo "SkyModderAI: Pre-downloading LOOT masterlist (skyrimse)..."
python3 loot_parser.py skyrimse
echo "SkyModderAI: Build complete."
