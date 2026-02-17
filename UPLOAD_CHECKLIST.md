# Upload Checklist

When manually uploading to GitHub (drag-and-drop), upload only these files. **Do not** upload the whole folder.

## ✅ Upload

**Root:** `app.py` `conflict_detector.py` `game_versions.py` `knowledge_index.py` `list_builder.py` `loot_parser.py` `mod_recommendations.py` `mod_warnings.py` `quickstart_config.py` `search_engine.py` `system_impact.py` `web_search.py` `requirements.txt` `Procfile` `render.yaml` `run.sh` `build.sh` `.python-version` `LICENSE` `README.md` `.gitignore` `.env.example`

**static/** — `favicon.svg` `css/style.css` `js/app.js` `icons/` (all SVGs + logo-icons.js)

**templates/** — `auth.html` `error.html` `index.html` `profile.html` `success.html` `verified.html`

## ❌ Do not upload

- `.env` — secrets
- `venv/` — recreated by `pip install`
- `users.db` — user data
- `__pycache__/` `data/*.yaml` `data/*_mod_database.json` `.cursor/`
