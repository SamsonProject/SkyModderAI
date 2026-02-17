# SkyModderAI

**Intelligent Load Order Analysis for Modded Games**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9-3.12](https://img.shields.io/badge/python-3.9--3.12-blue.svg)](https://www.python.org/downloads/)
[![CI](https://github.com/SamsonProject/SkyModderAI/actions/workflows/ci.yml/badge.svg)](https://github.com/SamsonProject/SkyModderAI/actions/workflows/ci.yml)
[![Coverage](https://codecov.io/gh/SamsonProject/SkyModderAI/branch/main/graph/badge.svg)](https://codecov.io/gh/SamsonProject/SkyModderAI)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![Docker](https://img.shields.io/badge/docker-ready-blue.svg)](https://www.docker.com/)

SkyModderAI is an advanced tool for analyzing and optimizing mod load orders for Bethesda games. It helps you identify conflicts, missing requirements, and provides intelligent suggestions for load order optimization.

## 🌟 Features

- **Load Order Analysis**: Automatically detects conflicts and issues in your mod load order
- **Multi-Game Support**: Works with Skyrim (LE/SE/AE/VR), Fallout 4, and Starfield
- **Intelligent Suggestions**: AI-powered recommendations for load order optimization
- **Real-time Feedback**: Get instant analysis as you build your mod list
- **CLI and Web Interface**: Choose your preferred way to interact with the tool
- **Open Source**: Completely free and open source under the MIT License
- **Privacy Focused**: All processing happens locally - your mod lists never leave your machine

## 🚀 Quick Start

### Prerequisites
- Python 3.9 or higher
- Git
- pip (Python package manager)

### Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/SamsonProject/SkyModderAI.git
   cd SkyModderAI
   ```

2. **Create and activate a virtual environment**:
   ```bash
   # On Windows
   python -m venv venv
   .\venv\Scripts\activate
   
   # On macOS/Linux
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application**:
   ```bash
   # Start the web interface
   python app.py
   ```
   Then open your browser to `http://localhost:5000`

## 🛠️ Usage

### Web Interface
1. Launch the application with `python app.py`
2. Open `http://localhost:5000` in your browser
3. Paste your load order or select a file to analyze
4. Review the analysis and follow the recommendations

### Command Line Interface
```bash
# Analyze a load order file
python -m skymodderai analyze path/to/loadorder.txt --game skyrimse

# Get help with commands
python -m skymodderai --help
```

## 📚 Documentation

For detailed documentation, please visit our [documentation site](https://samsonproject.github.io/SkyModderAI/).

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guidelines](CONTRIBUTING.md) for details on how to contribute to the project.

### Development Setup

1. Fork the repository
2. Create a new branch for your feature
3. Make your changes
4. Run tests: `pytest`
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- LOOT team for their amazing work on load order optimization
- The modding community for their support and feedback
- All contributors who have helped improve SkyModderAI

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
cd SkyModderAI
./run.sh
```
Or with Make: `make install && make run`

**Windows:** Double-click `run.bat` or in PowerShell: `.\run.ps1`

**Docker:**
```bash
docker build -t skymodderai . && docker run -p 5000:5000 skymodderai
```

**Manual steps (any platform):**
```bash
# Clone the repository
git clone https://github.com/SamsonProject/SkyModderAI.git
cd SkyModderAI

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
   SKYMODDERAI_DEV_PRO=1
   ```
3. Restart the app. You'll get full Pro: web search fallback, AI chat (requires `OPENAI_API_KEY`), Live Fix Guide, game folder scan.

To test Pro for a specific email only:
```env
SKYMODDERAI_TEST_PRO_EMAIL=your@email.com
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
SKYMODDERAI_OPENCLAW_ENABLED=0
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
SKYMODDERAI_OFFLINE_MODE=1
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

- High fences by default (`SKYMODDERAI_OPENCLAW_ENABLED=0` until you intentionally turn it on)
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
SkyModderAI/
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
