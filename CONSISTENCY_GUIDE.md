# Code Notes

Stuff to know when working on this.

---

**Type hints** - Every file needs `from __future__ import annotations` at the top. Add hints to functions.

**Formatting** - 100 char lines, 4 spaces, double quotes. Run `pre-commit run --all-files` before committing.

**Imports** - Future, stdlib, third-party, local. Logger after imports.

**Naming** - `snake_case` for files/functions, `UPPER_CASE` for constants, `PascalCase` for classes.

**Comments** - Explain why. Use `# FIXME:` for broken stuff, `# TODO:` for later, `# NOTE:` for important details.

**Errors** - Use exceptions from `exceptions.py`. Log them.

**Database** - Use `from db import get_db`. Don't import sqlite3 directly.

**Tests** - `test_*.py` in `tests/`. Run with `pytest`.

**Security** - Validate input. Don't commit secrets.

---

That's it. The code itself shows you how everything works.
