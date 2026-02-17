# SkyModderAI — Functionality Audit

**Date:** February 2025  
**Scope:** Backend routes, frontend flows, integrations, data model, gaps.

---

## 1. Core Features — Status

| Feature | Status | Notes |
|---------|--------|-------|
| **Mod list analysis** | ✅ Working | `/api/analyze` — conflicts, load order, system impact, mod warnings |
| **Mod search** | ✅ Working | `/api/mod-search` — BM25, LOOT data, Pro web fallback |
| **Conflict detection** | ✅ Working | `conflict_detector.py` + LOOT parser, 9 tests |
| **Suggested load order** | ✅ Working | From analysis payload, copy/apply buttons |
| **Heaviest mods ranking** | ✅ Working | `system_impact.py`, free for all tiers |
| **Mod warnings** | ✅ Working | Plugin limit, VRAM, complexity via `mod_warnings.py` |
| **Game version picker** | ✅ Working | `/api/games/<id>/game-versions` |
| **Masterlist version picker** | ✅ Working | `/api/games/<id>/masterlist-versions` |
| **Refresh masterlist** | ✅ Working | `/api/refresh-masterlist` (POST) |
| **Sample mod list** | ✅ Working | `/api/sample-mod-list?game=` |
| **Quick Start** | ✅ Working | `/api/quickstart` — dynamic per-game links |
| **Build a List** | ✅ Working | `/api/list-preferences/options`, `/api/build-list` |
| **Share link** | ✅ Working | `?share=<base64>` loads list from URL |

---

## 2. Pro Features — Status

| Feature | Status | Notes |
|---------|--------|-------|
| **AI chat** | ✅ Working | `/api/chat` — requires `OPENAI_API_KEY` + Pro tier |
| **Live Fix Guide** | ✅ Working | Built from analysis, updates as you chat |
| **Game folder scan** | ✅ Working | `/api/scan-game-folder` — Pro only |
| **Dev Tools** | ✅ Working | `/api/dev-analyze` — GitHub repo, upload, paste |
| **Web search fallback** | ✅ Working | `/duckduckgo-search` when no DB matches |
| **Save & load mod lists** | ⚠️ Local only | Stored in `localStorage`; Pro gate only. No server-side sync. |
| **AI multiple setups** | ✅ Working | Build a List: Pro gets AI-generated setups |

---

## 3. Auth & Payments — Status

| Feature | Status | Notes |
|---------|--------|-------|
| **Email/password signup** | ✅ Working | `/api/signup` + verification email |
| **Email verification** | ✅ Working | `/verify-email?token=` → `/verified` |
| **Login** | ✅ Working | `/api/login` |
| **Logout** | ✅ Working | `/logout` |
| **Google OAuth** | ✅ Working | `/auth/google` → callback; requires `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `BASE_URL` |
| **Stripe checkout** | ✅ Working | `/api/create-checkout` → Stripe Checkout |
| **Webhook** | ✅ Working | `/webhook` — `invoice.paid`, `payment_failed`, `subscription.deleted`, `checkout.session.completed` |
| **Payment success** | ✅ Working | `/payment-success` |
| **Billing portal** | ✅ Working | `/billing-portal` — Stripe customer portal |
| **Session management** | ✅ Working | `/api/sessions`, revoke, revoke-others |
| **API keys** | ✅ Working | `/api/developer/keys` — create, list, revoke |

---

## 4. Community — Status

| Feature | Status | Notes |
|---------|--------|-------|
| **List posts** | ✅ Working | `/api/community/posts` — sort=new\|top\|hot |
| **Create post** | ✅ Working | Login required, content filter |
| **Reply** | ✅ Working | `/api/community/posts/<id>/replies` |
| **Vote** | ✅ Working | `/api/community/posts/<id>/vote` — 1, -1, 0 |

---

## 5. API Endpoints — Completeness

| Endpoint | Method | Auth | Rate Limit |
|----------|--------|------|------------|
| `/api/games` | GET | No | — |
| `/api/games/<id>/game-versions` | GET | No | — |
| `/api/games/<id>/masterlist-versions` | GET | No | — |
| `/api/mod-search` | GET | No | Search |
| `/api/analyze` | POST | No | Analyze |
| `/api/v1/analyze` | POST | API key | Analyze |
| `/api/recommendations` | GET/POST | No | — |
| `/api/quickstart` | GET | No | — |
| `/api/list-preferences/options` | GET | No | — |
| `/api/build-list` | POST | No | Build-list |
| `/api/refresh-masterlist` | POST | No | API |
| `/api/sample-mod-list` | GET | No | — |
| `/api/link-preview` | GET | No | API |
| `/api/community/posts` | GET/POST | Post=login | Community |
| `/api/community/posts/<id>/replies` | POST | Login | Community |
| `/api/community/posts/<id>/vote` | POST | Login | — |
| `/api/chat` | POST | Pro | Chat |
| `/api/scan-game-folder` | POST | Pro | — |
| `/api/dev-analyze` | POST | Pro | — |
| `/api/search` | GET | No | — |
| `/api/ai-context` | GET/POST | No | — |
| `/api/search-solutions` | GET | No | — |
| `/api/resolve` | GET | No | — |
| `/api/check-tier` | GET | No | — |
| `/api/specs` | GET/POST | No | — |
| `/api/specs/parse-steam` | POST | No | — |
| `/api/create-checkout` | POST | Verified | — |
| `/api/sessions` | GET | Login | — |
| `/api/developer/keys` | GET/POST | Login | — |
| `/api/developer/keys/<id>` | DELETE | Login | — |

---

## 6. Gaps & Inconsistencies

### 6.1 Save & Load Mod Lists — Not Server-Side

- **Current:** `localStorage` only; Pro gate redirects to signup if not Pro.
- **Gap:** Pro users lose saved lists when switching devices or clearing browser data.
- **Plan (from LIST_FEATURE_PLAN.md):** `GET/POST /api/list-preferences` — Pro: cloud, Free: localStorage. Not implemented.

### 6.2 Rate Limiting — Per-Worker

- **Current:** In-memory `defaultdict(list)`; resets on restart.
- **Multi-worker:** Each worker has its own store; limits are effectively multiplied by worker count.
- **Recommendation:** Redis-backed limiter for production (e.g. `Flutter-Limiter[redis]`).

### 6.3 Link Preview — Domain Whitelist

- **Current:** `_LINK_PREVIEW_ALLOWED_DOMAINS` — Nexus, LOOT, xEdit, Reddit, etc.
- **Gap:** New domains require code change; no admin UI.

### 6.4 No Server-Side Saved Lists Table

- **DB tables:** `users`, `user_sessions`, `api_keys`, `community_posts`, `community_replies`, `community_votes`, `user_specs`.
- **Missing:** `user_saved_lists` or similar for Pro cloud sync.

### 6.5 Dev Tools — GitHub Fetch

- **Current:** Fetches public repo via GitHub API; no auth required.
- **Rate limits:** GitHub API has rate limits; no proxy/caching.

---

## 7. Frontend — Element Binding

- **Elements object:** 20+ IDs; all present in `index.html`.
- **Lazy refs:** Many `getElementById` calls inline; not all in `elements`.
- **Error handling:** Most fetch calls use `.catch()` or `res.ok` checks; some use `alert()` for errors.

---

## 8. Test Coverage

| Area | Tests | Coverage |
|------|-------|----------|
| `conflict_detector` | 9 tests | `parse_mod_list_text`, `ConflictDetector` |
| `app.py` | 0 | No route/integration tests |
| `loot_parser` | 0 | No tests |
| `search_engine` | 0 | No tests |
| `list_builder` | 0 | No tests |
| `system_impact` | 0 | No tests |
| `mod_warnings` | 0 | No tests |
| `knowledge_index` | 0 | No tests |

---

## 9. Environment & Configuration

| Required | Optional |
|----------|----------|
| `SECRET_KEY` | `STRIPE_*` (payments) |
| `FLASK_ENV` (production) | `OPENAI_API_KEY` (AI chat) |
| — | `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `BASE_URL` |
| — | `MAIL_*` (verification email) |
| — | `SKYMODDERAI_DEV_PRO`, `SKYMODDERAI_TEST_PRO_EMAIL` (dev) |

---

## 10. Pruning (Neurological-Style Context Reduction)

**Module:** `pruning.py`

Input and output pruning for AI agents, inspired by synaptic pruning. Reduces context volume while preserving signal.

- **Input pruning:** Before sending context to chat/game-folder scan, caps info-level conflicts at 12, trims when over limit. **Invariants:** errors and warnings are never cut; mod names and suggested actions preserved.
- **Output pruning:** Optional distillation of AI replies for Fix Guide (keeps full reply for chat display).
- **Game folder:** Tree and key files truncated per-file when large.
- **Config:** `PRUNING_ENABLED=1` (default), `PRUNING_MAX_CONTEXT_CHARS=12000`.

---

## 11. Recommendations

1. **Save lists:** Add `user_saved_lists` table and API for Pro cloud sync.
2. **Rate limiting:** Implement Redis-backed limiter for multi-worker.
3. **Tests:** Add API tests for `/api/analyze`, `/api/mod-search`, auth flows.
4. **LOOT parser:** Add tests for download, parse, cache.
5. **Health check:** `/health` already returns LOOT data status; use for monitoring.
6. **Error pages:** 404/500 handlers exist; API returns JSON, HTML returns `error.html`.

---

## Summary

**Working:** Core analysis, mod search, auth, Stripe, community, Quick Start, Build a List, Dev Tools, AI chat, game folder scan, Live Fix Guide.  
**Partial:** Save/load lists (local only, no cloud).  
**Technical debt:** In-memory rate limit, limited test coverage.
