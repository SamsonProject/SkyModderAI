# SkyModderAI — Multiplatform convenience targets
# Usage: make [target]
# Works on Linux, macOS, and Windows (with make installed, e.g. via Chocolatey)

.PHONY: run install test build clean loot help lint format check coverage ci

# Default Python (respects .python-version if using pyenv)
PYTHON ?= python3
VENV := venv
VENV_PY := $(VENV)/bin/python
VENV_PIP := $(VENV)/bin/pip
# Windows: venv\Scripts\python.exe
ifeq ($(OS),Windows_NT)
	VENV_PY := $(VENV)/Scripts/python.exe
	VENV_PIP := $(VENV)/Scripts/pip.exe
endif

help:
	@echo "SkyModderAI — Available targets:"
	@echo "  make install   — Create venv and install dependencies"
	@echo "  make run       — Start the app (http://127.0.0.1:5000)"
	@echo "  make loot      — Download LOOT masterlist for skyrimse"
	@echo "  make loot GAME=fallout4 — Download for specific game"
	@echo "  make test      — Run pytest"
	@echo "  make build     — Install deps + pre-download LOOT (for deploy)"
	@echo "  make clean     — Remove venv, __pycache__, .pytest_cache"
	@echo ""
	@echo "Development targets:"
	@echo "  make lint      — Run Ruff linter"
	@echo "  make format    — Format code with Ruff"
	@echo "  make check     — Run lint + tests (CI check)"
	@echo "  make coverage  — Run tests with coverage report"
	@echo "  make ci        — Full CI simulation (lint + test + coverage)"
	@echo ""
	@echo "Examples:"
	@echo "  make install && make run"
	@echo "  make loot GAME=starfield"
	@echo "  make ci"

install:
	@echo "Creating virtual environment..."
	$(PYTHON) -m venv $(VENV)
	@echo "Installing dependencies..."
	$(VENV_PIP) install -q -r requirements.txt
	@echo "Done. Run 'make run' to start."

run:
	@test -d $(VENV) || { echo "Run 'make install' first."; exit 1; }
	@test -f data/skyrimse_mod_database.json || (echo "Downloading LOOT masterlist (skyrimse)..."; $(VENV_PY) loot_parser.py skyrimse)
	@echo "Starting SkyModderAI on http://127.0.0.1:5000"
	$(VENV_PY) app.py

loot: install
	@GAME=$${GAME:-skyrimse}; \
	echo "Downloading LOOT masterlist ($$GAME)..."; \
	$(VENV_PY) loot_parser.py $$GAME

test: install
	$(VENV_PY) -m pytest tests/ -v

build: install
	$(VENV_PY) loot_parser.py skyrimse
	@echo "Build complete."

clean:
	rm -rf $(VENV) __pycache__ .pytest_cache .ruff_cache
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	@echo "Cleaned."

# Development targets
lint: install
	$(VENV_PY) -m ruff check .

format: install
	$(VENV_PY) -m ruff format .

check: install
	@echo "Running linter..."
	$(VENV_PY) -m ruff check .
	@echo "Running tests..."
	$(VENV_PY) -m pytest tests/ -v

coverage: install
	$(VENV_PY) -m pytest tests/ -v --cov=. --cov-report=term-missing

ci: install
	@echo "=== CI Simulation ==="
	@echo ""
	@echo "Step 1: Linting..."
	$(VENV_PY) -m ruff check .
	@echo ""
	@echo "Step 2: Running tests..."
	$(VENV_PY) -m pytest tests/ -v --tb=short
	@echo ""
	@echo "Step 3: Coverage report..."
	$(VENV_PY) -m pytest tests/ -v --cov=. --cov-report=term-missing --cov-report=xml
	@echo ""
	@echo "=== CI Complete ==="
