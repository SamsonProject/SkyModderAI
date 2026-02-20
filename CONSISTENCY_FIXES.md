# What Got Fixed

**Date:** 2026-02-19

Consistency fixes across the codebase. Nothing deleted, just organized.

---

## Database Connections

`shopping_service.py` was creating its own SQLite connections. Now it uses `db.py` like everything else.

---

## Type Hints

`app.py` helper functions were missing type hints. Added them:

```python
def _load_game_versions_data() -> dict[str, Any]:
def get_versions_for_game(game_id: str) -> dict[str, Any]:
def get_default_version(game_id: str) -> str:
def get_version_info(game_id: str, version: str) -> Optional[dict[str, Any]]:
def get_version_warning(game_id: str, version: str) -> Optional[dict[str, str]]:
def _redact_email(email: Optional[str]) -> str:
```

---

## Logger Position

`config.py` had the logger in the wrong spot. Moved it after imports.

---

## Exception Logging

Several files had silent `except Exception:` blocks. Now they all log:

```python
except Exception as e:
    logger.warning(f"Unexpected error: {e}")
    return None
```

Fixed in: `auth_utils.py`, `web_search.py`, `cache_service.py`, `scheduler.py`

---

## Comment Markers

Added markers to organize long comments in `pruning.py` and `context_threading.py`:

- `# CONTEXT:` - Background and why
- `# INVARIANT:` - Must never change
- `# CONFIG:` - Configuration notes
- `# ARCHITECTURE:` - Design stuff
- `# USAGE:` - How to use

Nothing deleted. Just labeled.

---

## Files Changed

```
app.py               - Type hints
config.py            - Logger position  
shopping_service.py  - Database access
auth_utils.py        - Exception logging
web_search.py        - Exception logging
cache_service.py     - Exception logging
scheduler.py         - Exception logging
pruning.py           - Comment markers
context_threading.py - Comment markers
```

10 files, ~100 lines.

---

## Validation

Everything passes:
- Python syntax ✓
- Imports work ✓
- Black formatting ✓
- Ruff linting ✓

---

The guide's been rewritten to match what this actually is: a free tool for modders, kept running by ad revenue from businesses. Not a SaaS product. Not a startup pitch. Just code that works.
