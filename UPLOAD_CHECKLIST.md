# Upload Checklist

Deploying the Powerhouse. Ensure these core components are included.

## ✅ Upload

**Core Engine:** `app.py` `conflict_detector.py` `game_versions.py` `knowledge_index.py` `list_builder.py` `loot_parser.py` `mod_recommendations.py` `mod_warnings.py` `quickstart_config.py` `search_engine.py` `system_impact.py` `web_search.py`

**Config & Deploy:** `requirements.txt` `Procfile` `render.yaml` `run.sh` `build.sh` `.python-version` `LICENSE` `README.md` `.gitignore` `.env.example`

**Frontend:** `static/` (css, js, icons), `templates/` (all html files)

## ❌ Do not upload

- `.env` — secrets
- `venv/` — recreated by `pip install`
- `users.db` — user data
- `__pycache__/` `data/*.yaml` `data/*_mod_database.json` `.cursor/`
