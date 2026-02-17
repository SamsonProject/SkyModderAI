# SkyModderAI Implementation Checklist

**Modder-minded improvements and modern software practices.**  
Generated from deep codebase review.

---

## ✅ Implemented

### 1. **Bug fix: conflict_detector patch check**
- **Issue:** `mod_name` was undefined in the patch-available loop (would raise `NameError`).
- **Fix:** Replaced with `mod.name` in the `ModConflict` message and `affected_mod`.
- **File:** `conflict_detector.py`

### 2. **Environment template**
- **Issue:** `.env.example` lacked Google OAuth and `BASE_URL`.
- **Fix:** Added `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `BASE_URL`.
- **File:** `.env.example`

### 3. **Rate limiting**
- **Issue:** API endpoints could be abused (analyze, search, chat, refresh).
- **Fix:** In-memory rate limiter (per-worker) applied in production:
  - Analyze: 30 req/min
  - Search: 60 req/min
  - Chat, refresh, community: throttled
- **Note:** For multi-worker production, use Redis (`Flask-Limiter[redis]`).
- **File:** `app.py`

### 4. **Security headers**
- **Issue:** Missing standard security headers.
- **Fix:** `X-Content-Type-Options`, `X-Frame-Options`, `X-XSS-Protection`, `Referrer-Policy` in production.
- **File:** `app.py`

### 5. **Tests**
- **Issue:** No automated tests.
- **Fix:** `pytest` + `tests/test_conflict_detector.py`:
  - `parse_mod_list_text`: plugins.txt, MO2, Vortex, comments, paths
  - `ConflictDetector`: unknown mod, missing requirement
- **Run:** `pytest tests/ -v`

### 6. **PWA manifest**
- **Issue:** No installability for mobile/desktop.
- **Fix:** `static/manifest.json` + `/manifest.json` route with correct MIME type.
- **File:** `static/manifest.json`, `app.py`, `templates/index.html`

### 7. **Pro+ AI copy**
- **Issue:** "Coming soon" when feature is live for Pro+ users.
- **Fix:** Updated copy to "available" / "upgrade to add AI assistance".
- **Files:** `templates/index.html`, `static/js/app.js`, `app.py`

### 8. **Checkout modal**
- **Fix:** Removed reference to non-existent `checkout-email` input in `openCheckoutModal()`.
- **File:** `static/js/app.js`

---

## 🔮 Future improvements (brainstorm)

### High-end / modern tooling

| Area | Suggestion | Rationale |
|------|------------|-----------|
| **Search** | Elasticsearch / Meilisearch / Typesense | Full-text search, typo tolerance, faceting for large mod DBs |
| **Caching** | Redis | Shared cache for LOOT data, rate limits, sessions across workers |
| **Background jobs** | Celery / RQ / Dramatiq | Masterlist refresh, web search, email sending off request path |
| **Observability** | OpenTelemetry, Sentry | Tracing, error tracking, performance monitoring |
| **API versioning** | `/api/v2/` | Stable public API for integrations and AI tools |
| **Frontend** | Alpine.js / HTMX / React | Progressive enhancement, less custom JS |
| **Testing** | Playwright / Cypress | E2E tests for critical flows |
| **CI/CD** | GitHub Actions | Lint, test, deploy on push |
| **Database** | PostgreSQL | User data, API keys, sessions at scale |
| **Vector search** | pgvector / Pinecone | Semantic mod search, "mods like this" |

### Modder-specific

- **Quick Start** – Now dynamic via `/api/quickstart`; links come from `quickstart_config.py` (no hard-coding in templates)
- **Nexus API integration** – Mod images, download counts, endorsements for recommendations
- **Wabbajack list parsing** – Import from Wabbajack mod lists
- **Conflict graph** – Visual dependency/conflict graph (D3.js, Cytoscape)
- **Mod version tracking** – Compare user list vs latest Nexus versions
- **Community-driven rules** – User-submitted LOOT-style metadata (with moderation)

---

## Quick reference

```bash
# Run tests
pytest tests/ -v

# Run app locally
./run.sh

# Deploy (Render)
# Uses render.yaml; set env vars in dashboard
```
