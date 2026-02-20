# SkyModderAI

Modding tool for Bethesda games. Analyzes load orders, finds conflicts, suggests fixes.

Free to use. Runs locally. No accounts needed.

---

## What It Does

- Checks your mod list for conflicts
- Parses LOOT data
- Suggests fixes based on community knowledge
- Exports guides as PDF/HTML/Markdown

---

## Quick Start

```bash
git clone https://github.com/SamsonProject/SkyModderAI.git
cd SkyModderAI
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
python3 app.py
```

Open http://localhost:5000 in your browser.

---

## How It Works

Reads your mod list, checks against known conflicts, shows what needs fixing. Uses cached data so it's fast. Updates from Nexus Mods and Reddit every few hours.

---

## Files That Matter

- `app.py` - Main application
- `conflict_detector.py` - Finds conflicts
- `loot_parser.py` - Reads LOOT data
- `search_engine.py` - Searches mod database
- `db.py` - Database stuff

---

## Testing

```bash
pytest tests/
```

---

## Contributing

Make a change, test it, submit a PR. Format with `pre-commit run --all-files`.

---

## Why This Exists

I spent way too many hours debugging mod conflicts that someone else already solved. This tool finds those solutions automatically. If it saves you even one afternoon of troubleshooting, it worked.

---

That's about it. Download it, run it, mod safely.
