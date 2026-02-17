# SkyModderAI

**Paste your load order. Get answers.**

I've been modding since 2012—right after Skyrim launched. Hundreds of mods. One crash. No idea why. Sound familiar? SkyModderAI is the tool I built so we don't have to guess anymore—paste your list, get instant conflict detection, missing requirements, load order fixes, dirty edit warnings. Same LOOT data the community trusts. Skyrim, Fallout, Starfield. Less time debugging, more time playing.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![CI](https://github.com/SamsonProject/SkyModderAI/actions/workflows/ci.yml/badge.svg)](https://github.com/SamsonProject/SkyModderAI/actions/workflows/ci.yml)
[![Deployed on Render](https://img.shields.io/badge/Deployed_on-Render-46a2f1.svg)](https://render.com)
[![Stars](https://img.shields.io/github/stars/SamsonProject/SkyModderAI?style=social)](https://github.com/SamsonProject/SkyModderAI)

## Live App

[Try SkyModderAI →](https://skymodderai.onrender.com)

> **Note:** The live URL may vary by deployment. Check your `render.yaml` or hosting config for the actual domain.

## What It Does

**For everyone:** Paste your load order (MO2, Vortex, plugins.txt, or messy mixed text). Get instant conflict detection—missing requirements, load order violations, incompatibilities, dirty edits. Same LOOT masterlist data. Skyrim SE/LE/VR, Oblivion, Fallout 3/NV/4, Starfield. Heaviest mods ranking. Suggested load order. Auto-format + live match preview for typed lists. Copy or download your report (`.txt` + `.json`). Free.

**For new modders:** Quick Start guides you to your mod list, essential tools (MO2, LOOT, xEdit), and where to learn. Live link preview supports in-app reading, and internal links render as full live page previews.

**For heavy modders:** Mod search with the same LOOT data. Masterlist version picking for older setups. Build a List from game-aware preferences with automatic Analyze handoff. APIs for automation.

**For mod authors (Pro):** Dev Tools—drop your Papyrus, configs, or repo. AI checks runtime compatibility before you ship.

**Pro extras ($5/mo):** Live Fix Guide that updates as you chat. AI chat about your conflicts. Game folder scan beyond load order. Web search when the DB has few matches. Save & load mod lists. Keeps the lights on so I can keep building.

**OpenClaw Lab (separate tier):** Experimental, high-risk local automation workflows behind explicit guardrails. Designed around "personal space" boundaries: dedicated workspace folder, strict acknowledgements, and manual verification.



*Paste. Analyze. Get answers.*



*Conflicts, load order, heaviest mods—all in one place.*

## Configuration

### Required Environment Variables

- `BASE_URL` - Your public-facing URL without a trailing slash (e.g., `https://skymodderai.com`)
  - **Important**: This must match exactly what's registered in Google Cloud Console and GitHub OAuth settings
  - Required for OAuth to work in production
  - No trailing slash
  - Example: `BASE_URL=https://skymodderai.com`

### Email Configuration
- `MAIL_SERVER` - SMTP server hostname (e.g., `smtp.sendgrid.net`)
- `MAIL_PORT` - SMTP port (typically `587` for TLS, `465` for SSL)
- `MAIL_USERNAME` - SMTP username
- `MAIL_PASSWORD` - SMTP password
- `MAIL_USE_TLS` - Set to `true` for TLS encryption
- `MAIL_DEFAULT_SENDER` - Default sender email address

### OAuth Configuration
#### Google OAuth
- `GOOGLE_CLIENT_ID` - From Google Cloud Console
- `GOOGLE_CLIENT_SECRET` - From Google Cloud Console
- Add authorized redirect URI in Google Cloud Console: `{BASE_URL}/auth/google/callback`

#### GitHub OAuth
- `GITHUB_CLIENT_ID` - From GitHub OAuth App settings
- `GITHUB_CLIENT_SECRET` - From GitHub OAuth App settings
- Set callback URL in GitHub OAuth App settings: `{BASE_URL}/auth/github/callback`

### Security
- `SECRET_KEY` - Long random string for session encryption (generate with: `python3 -c "import secrets; print(secrets.token_hex(32))"`)
- `SESSION_COOKIE_SECURE` - Set to `true` in production
- `SESSION_COOKIE_HTTPONLY` - Set to `true` for security
- `SESSION_COOKIE_SAMESITE` - Set to `'Lax'` for OAuth compatibility

For a complete list of all available configuration options, see `.env.example` in the project root.

## Quick Start

### Run Locally

**Linux / macOS / WSL:**
```bash
git clone https://github.com/SamsonProject/SkyModderAI.git
cd modcheck
./run.sh
```
Or with Make: `make install && make run`

**Windows:** Double-click `run.bat` or in PowerShell: `.\run.ps1`

**Docker:**
```bash
docker build -t modcheck . && docker run -p 5000:5000 modcheck
```

**Manual steps (any platform):**
```bash
# Clone the repository
git clone https://github.com/SamsonProject/SkyModderAI.git
cd modcheck

# Create venv and install dependencies (use venv so Stripe, dotenv work)
python3 -m venv venv
./venv/bin/pip install -r requirements.txt   # Windows: venv\Scripts\pip install -r requirements.txt

# Download latest LOOT masterlist data
./venv/bin/python loot_parser.py skyrimse    # Windows: venv\Scripts\python loot_parser.py skyrimse

# Run the app
./venv/bin/python app.py                     # Windows: venv\Scripts\python app.py

# Or to run on a specific port (e.g., 10000):
# ./venv/bin/python -m flask run --port=10000   # Windows: venv\Scripts\python -m flask run --port=10000
```

Open **http://127.0.0.1:10000** in your browser.

> **Note:** Use the venv (`./venv/bin/python`) so Stripe and python-dotenv are available. `run.sh` does this automatically.

### Testing Pro features locally

When running locally (not in production), you can simulate Pro access without paying:

1. **Log in** with any account (or create one).
2. Add to your `.env`:
   ```env
   MODCHECK_DEV_PRO=1
   ```
3. Restart the app. You'll get full Pro: web search fallback, AI chat (requires `OPENAI_API_KEY`), Live Fix Guide, game folder scan.

To test Pro for a specific email only:
```env
MODCHECK_TEST_PRO_EMAIL=your@email.com
```

These overrides only apply when `FLASK_ENV` is not `production`.

### Deploy to Render

1. Fork this repository
2. Go to [Render.com](https://render.com) → New Web Service
3. Connect your forked repo
4. Set **Build Command:** `pip install -r requirements.txt && python3 loot_parser.py skyrimse` (pre-downloads LOOT data so cold start is instant)
5. Add the required environment variables (see below)
6. Deploy

Alternatively, use the included `render.yaml` blueprint for infrastructure-as-code deployment.

Health endpoint for uptime checks:

```bash
GET /healthz
```

Runtime capability snapshot (great for online/offline testing):

```bash
GET /api/platform-capabilities
```

## Configuration

### Environment Variables

Add these in your Render dashboard:

```env
FLASK_ENV=production                   # Enables secure session cookies over HTTPS
STRIPE_SECRET_KEY=sk_live_...
STRIPE_PUBLISHABLE_KEY=pk_live_...     # Optional for now
STRIPE_PRO_PRICE_ID=price_...          # Important: Use the Price ID (not Product ID)
STRIPE_OPENCLAW_PRICE_ID=price_...     # Optional: OpenClaw Lab tier
STRIPE_WEBHOOK_SECRET=whsec_...        # Required for webhook signature verification (Stripe Dashboard → Webhooks)
SECRET_KEY=your_super_long_random_string
```

Generate a strong secret key:
```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

**STRIPE_WEBHOOK_SECRET:** Configure your Stripe webhook endpoint to `https://your-domain/webhook` and copy the signing secret. Without it, webhook signatures won't be verified (subscription updates may fail).

**Verification email:** Signup sends a verification link before users can go to checkout. Set these env vars to send real email:

```env
MAIL_FROM=noreply@yourdomain.com
MAIL_HOST=smtp.yourprovider.com
MAIL_PORT=587
MAIL_USER=your-smtp-user
MAIL_PASSWORD=your-smtp-password
```

- **Gmail:** Use `smtp.gmail.com`, port `587`, and an [App Password](https://support.google.com/accounts/answer/185833) (not your regular password—requires 2FA).
- **SendGrid / Mailgun / etc.:** Use their SMTP host and credentials from the dashboard.
- **Port 465 (SSL):** Set `MAIL_USE_SSL=true` or use port `465`; the app will use SMTP_SSL.
- **If unset:** The verification link is logged server-side (dev only); users still see "Check your email."

**Web search (Pro feature):** The web search fallback uses the `duckduckgo-search` Python package—no API key required. It scrapes DuckDuckGo directly. Install via `pip install -r requirements.txt`. If the package is missing, web search is disabled and Pro users get DB-only results.

**OpenClaw safety controls (optional, default OFF):**

```env
MODCHECK_OPENCLAW_ENABLED=0
OPENCLAW_SANDBOX_ROOT=./openclaw_workspace
OPENCLAW_MAX_FILES=500
OPENCLAW_MAX_BYTES=52428800
OPENCLAW_MAX_PATH_DEPTH=10
OPENCLAW_MAX_PATH_LENGTH=220
OPENCLAW_REQUIRE_SAME_IP=1
```

OpenClaw should remain disabled unless you intentionally operate the experimental tier and understand the risks.

**Offline-safe mode (optional):**

```env
MODCHECK_OFFLINE_MODE=1
```

When enabled, external link previews are disabled gracefully while internal links and core analysis features still work.

**Sign in with Google (optional):** To enable "Sign in with Google" on the login page:

1. Create OAuth 2.0 credentials in [Google Cloud Console](https://console.cloud.google.com/apis/credentials)
2. Add **Authorized redirect URIs** (exact match required):
   - Production: `https://your-domain.com/auth/google/callback`
   - Local: `http://localhost:5000/auth/google/callback` (or `http://127.0.0.1:5000/auth/google/callback`)
3. Set env vars:

```env
GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-client-secret
```

If you get `redirect_uri_mismatch`, the URI sent to Google doesn't match what's in the console. Set `BASE_URL=https://your-actual-domain.com` (no trailing slash) when behind a proxy or when the request host differs from your public URL.

Sessions are stored server-side (SQLite). Users can see and revoke devices on the Profile page and use "Trust this device" for 30-day sign-in.

**Developer API:** Logged-in users can create API keys from Profile → API keys (developer). Use a key to call the engine with a shorter, filtered JSON response:

- **Endpoint:** `POST /api/v1/analyze`
- **Auth:** `Authorization: Bearer <your_key>` or header `X-API-Key: <your_key>`
- **Body:** `{ "mod_list": "...", "game": "skyrimse" }` (same as the web analyze)
- **Response:** `game`, `mod_count`, `enabled_count`, `conflicts` (flat list with `severity`, `type`, `message`, `affected_mod`, `suggested_action`), `summary` (counts). No HTML report; unlimited mod analysis for all tiers.

**Search & AI APIs (no auth for read):**

- `GET /api/search?q=ordinator&game=skyrimse&for_ai=1` — BM25-ranked mod search with scores, snippets, `mod_info` (requirements, tags)
- `POST /api/modlist/normalize` — Parse messy mod list input and return normalized text + fuzzy/search-based match suggestions
- `GET /api/ai-context?game=skyrimse&query=ctd` — Structured knowledge (resolutions, esoteric solutions, game resources)
- `GET /api/quickstart?game=skyrimse` — Game-specific quick start links (tools, mod managers, unofficial patches, AppData paths)
- `GET /api/list-preferences/options?game=skyrimse` — Game-aware Build a List preference schema for the selected game
- `POST /api/build-list` — Generate preference-based mod list (optionally includes Pro AI setups)
- `GET /api/resolve?type=missing_requirement&game=skyrimse` — Resolution pattern for a conflict type
- `GET /api/search-solutions?q=ctd+skyrim&game=skyrimse` — Pro: web search for scattered fixes (Reddit, Nexus)
- `POST /api/feedback` — Submit bug reports, complaints, feature requests, praise, or questions
- `POST /api/satisfaction/survey` — Post-analysis helpfulness score (1-5)
- `GET /api/community/health` — Community pulse metrics (posts/replies/helpfulness/reports)
- `POST /api/community/reports` — Report a post or reply for moderation review
- `POST /api/activity/track` — Optional client-side activity telemetry for product iteration
- `GET /api/profile/dashboard` — Dynamic profile dashboard data (community stats, top tags, recent activity, suggested next actions)
- `GET /api/openclaw/policy` — OpenClaw policy surface (sandbox root, limits, warnings)
- `POST /api/openclaw/request-access` — OpenClaw tier acknowledgement gate (requires logged-in OpenClaw Lab user)
- `POST /api/openclaw/guard-check` — Dry-run policy validation for OpenClaw file operations
- `POST /api/openclaw/verify-grant` — Verify short-lived OpenClaw grant token
- `GET/POST /api/openclaw/permissions` — Get or grant scoped OpenClaw capabilities (launch, metrics, logs, internet research, sandbox writes)
- `POST /api/openclaw/plan/propose` — Build a permission-scoped improvement plan (propose only)
- `POST /api/openclaw/plan/execute` — Execute approved plan steps within sandbox constraints
- `POST /api/openclaw/loop/feedback` — Submit post-run telemetry/experience and receive next-loop suggestions
- `GET /api/openclaw/safety-status` — OpenClaw hardening score/checklist and immutable limits
- `GET /api/openclaw/capabilities` — Safe vs blocked capability map (explicitly blocks BIOS/firmware/kernel-level control)
- `GET /api/openclaw/install-manifest` — Companion install + permission prompt contract for local runtime integration
- `POST /api/dev-loop/suggest` — Samson dev companion loop (feature ideas + optimization actions + idle recommendation)
- `GET /ai-feed.json` — Machine-readable product feed for AI agents/aggregators
- `GET /api` — Human-readable API hub for developers and indexing
- `GET /api/information-map` — Machine-readable map of data flow (input -> processing -> storage -> action)
- `GET /sitemap.xml` — Search crawler discovery map for product/API/legal pages

## Pricing

Core analysis is free. Always. No paywall on your results—paste, analyze, copy, download. Pro ($5/mo) unlocks the AI helpers and keeps me building. OpenClaw Lab is a separate, higher-risk tier intended for advanced users who review the source and accept experimental constraints. Cancel anytime.

- **Free** — Unlimited analysis, conflict detection, heaviest mods ranking, suggested load order, copy & download report, Build a List with automatic Analyze handoff, community
- **Pro** — Live Fix Guide, AI chat, game folder scan, Dev Tools, web search fallback, save & load lists
- **OpenClaw Lab** — Everything in Pro + experimental local automation pathways gated by acknowledgements, sandbox policy, and explicit user responsibility

### OpenClaw safety posture

If you enable OpenClaw Lab in your deployment, keep these principles:

- High fences by default (`MODCHECK_OPENCLAW_ENABLED=0` until you intentionally turn it on)
- Dedicated workspace boundary (`OPENCLAW_SANDBOX_ROOT`) to respect the rest of the machine
- Explicit acknowledgements before access (`/api/openclaw/request-access`)
- Permission-scoped execution (`/api/openclaw/permissions`) and plan approval before execution
- Immutable guard-check + loop feedback (`/api/openclaw/guard-check`, `/api/openclaw/loop/feedback`)
- Public implementation transparency (encourage users to review source before buying)
- Plain-language + technical safety disclosures (`/safety`) for legal/software warnings

## Tech Stack

- **Backend:** Python + Flask
- **Frontend:** Vanilla JavaScript + HTML/CSS
- **Data:** LOOT Masterlist
- **Payments:** Stripe
- **Deployment:** Render

## Project Structure

```bash
modcheck/  # or skymodderai/
├── app.py                    # Main Flask application
├── conflict_detector.py      # Core conflict detection logic
├── game_versions.py          # Game executable version database
├── knowledge_index.py        # Conflict resolutions, esoteric solutions, AI context
├── list_builder.py           # Preference-based mod list generation
├── quickstart_config.py      # Game-specific quick start links (feeds /api/quickstart)
├── loot_parser.py            # Downloads and parses LOOT data (CLI: python3 loot_parser.py [game])
├── search_engine.py          # BM25 ranking, query expansion, inverted index
├── system_impact.py          # Heaviest mods ranking, VRAM/complexity estimates
├── web_search.py             # Pro: DuckDuckGo fallback for mod search
├── pruning.py                # Neurological-style context pruning for AI (input/output)
├── samson_fuel.py            # Structural extraction (privacy-respecting, no PII)
├── docs/                     # Architecture and research notes
├── run.sh                    # Local run (Linux/macOS/WSL)
├── run.bat                   # Local run (Windows CMD)
├── run.ps1                   # Local run (Windows PowerShell)
├── Makefile                  # make install, make run, make test
├── Dockerfile                # Docker image for reproducible runs
├── build.sh                  # Optional build script for deploy
├── render.yaml               # Render blueprint (optional IaC)
├── requirements.txt
├── Procfile
├── .env.example              # Env var template (copy to .env)
├── UPLOAD_CHECKLIST.md       # Manual GitHub upload guide
├── templates/
│   ├── index.html
│   ├── auth.html             # Login + signup (combined)
│   ├── verified.html
│   ├── success.html
│   ├── profile.html
│   ├── terms.html
│   ├── privacy.html
│   ├── safety.html
│   ├── api_hub.html
│   └── error.html
├── static/
│   ├── css/style.css
│   ├── js/app.js
│   ├── js/auth.js
│   ├── js/profile.js
│   ├── js/verified.js
│   ├── icons/                # Nexus, LOOT, xEdit, MO2, Vortex, Wabbajack SVGs + logo-icons.js
└── data/
    └── *_mod_database.json   # Cached LOOT data (per game, gitignored)
```

## Contributing

Contributions are welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for multiplatform setup. This is open source. The hosted version may offer Pro features as a paid service.

## License

MIT License — See [LICENSE](LICENSE) for details.

## Credits

- **LOOT Team** — The masterlist data that makes this possible
- **Bethesda** — The games we keep coming back to
- **Modding community** — 14+ years of shared knowledge

## Support

- **Email:** mcompchecker@gmail.com
- **Phone:** (206) 915-7203
- **Issues:** [GitHub Issues](https://github.com/SamsonProject/SkyModderAI/issues)
- **Legal:** [Terms](/terms) · [Privacy](/privacy) · [Safety](/safety)

## Support the Project

If this helps you get back to modding (or finally get a stable list), consider:
- Starring the repo
- Going Pro
- Reporting bugs or suggesting features

---

**Built by someone who's been there.** Happy modding.
