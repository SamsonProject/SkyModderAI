# Contributing to SkyModderAI

Thanks for your interest! This guide gets you running on any platform.

## Prerequisites

- **Python 3.8+** (3.11 recommended; see `.python-version`)
- Git

## Quick Start by Platform

### Linux / macOS / WSL

```bash
# Option 1: One-liner
./run.sh

# Option 2: Make (if you have make)
make install && make run

# Option 3: Manual
python3 -m venv venv
./venv/bin/pip install -r requirements.txt
./venv/bin/python loot_parser.py skyrimse
./venv/bin/python app.py
```

### Windows (CMD)

```cmd
run.bat
```

### Windows (PowerShell)

```powershell
.\run.ps1
```

### Windows (Make)

If you have [Make for Windows](https://gnuwin32.sourceforge.net/packages/make.htm) or Chocolatey (`choco install make`):

```cmd
make install
make run
```

## Common Tasks

| Task | Linux/macOS | Windows |
|------|-------------|---------|
| Run app | `./run.sh` or `make run` | `run.bat` or `run.ps1` |
| Run tests | `make test` or `./venv/bin/pytest` | `venv\Scripts\pytest` |
| Download LOOT data | `make loot` or `make loot GAME=fallout4` | `venv\Scripts\python loot_parser.py skyrimse` |
| Clean | `make clean` | Delete `venv`, `__pycache__` |

## Environment

Copy `.env.example` to `.env` and fill in values for Stripe, email, etc. See README for full config.

## Testing Pro Locally

Add to `.env`:
```
MODCHECK_DEV_PRO=1
```
Any logged-in user gets full Pro features (no payment).

## Code Style

- Ruff for linting: `ruff check .`
- Pytest for tests: `pytest tests/ -v`

## Submitting Changes

1. Fork the repo
2. Create a branch
3. Make your changes
4. Run tests
5. Open a PR
