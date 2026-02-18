"""
SkyModderAI - Mod Compatibility Checker
Main Flask application with improved security, error handling, and Stripe integration.
"""

import hashlib
import html
import json
import logging
import os
import re
import secrets
import smtplib
import sqlite3
from collections import OrderedDict, defaultdict
from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from functools import wraps
from time import time as _time
from typing import Optional
from urllib.parse import quote, urlencode, urljoin, urlparse

import requests
from flask import (
    Flask,
    Response,
    g,
    jsonify,
    make_response,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from itsdangerous import URLSafeTimedSerializer
from werkzeug.middleware.proxy_fix import ProxyFix
from werkzeug.security import check_password_hash, generate_password_hash

from config import config

# Local modules
from conflict_detector import ConflictDetector, parse_mod_list_text

# Shared constants - imported from constants.py
from constants import (
    MAX_INPUT_SIZE,
    PLUGIN_LIMIT,
    PLUGIN_LIMIT_WARN_THRESHOLD,
    RATE_LIMIT_ANALYZE,
    RATE_LIMIT_API,
    RATE_LIMIT_SEARCH,
    RATE_LIMIT_WINDOW,
)
from game_versions import (
    get_default_version,
    get_version_info,
    get_version_warning,
    get_versions_for_game,
)
from knowledge_index import (
    build_ai_context as build_knowledge_context,
)
from knowledge_index import (
    format_knowledge_for_ai,
    get_game_resources,
    get_resolution_for_conflict,
)
from list_builder import build_list_from_preferences, get_preference_options
from loot_parser import LOOTParser
from mod_recommendations import get_recommendations, get_recommendations_for_ai
from mod_warnings import get_mod_warnings
from openclaw_engine import (
    OPENCLAW_PERMISSION_SCOPES,
    build_openclaw_plan,
    suggest_loop_adjustments,
)
from search_engine import get_search_engine
from system_impact import (
    format_system_impact_for_ai,
    format_system_impact_report,
    get_system_impact,
)


# -------------------------------------------------------------------
# PII redaction for logs (never log emails, tokens, or customer data)
# -------------------------------------------------------------------
def _redact_email(email):
    """Redact email for safe logging. Returns e.g. 'u***@***'."""
    if not email or not isinstance(email, str):
        return "***"
    e = email.strip().lower()
    if "@" not in e:
        return "***"
    local, domain = e.split("@", 1)
    if len(local) <= 1:
        return "*@***"
    return f"{local[0]}***@{domain[0]}***"


# -------------------------------------------------------------------
# Configuration and logging
# -------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Stripe integration
STRIPE_AVAILABLE = False
if config.PAYMENTS_ENABLED:
    try:
        import stripe

        stripe.api_key = config.STRIPE_SECRET_KEY
        if config.STRIPE_WEBHOOK_SECRET:
            logger.info("Stripe payments enabled with webhook verification")
        else:
            logger.warning("Stripe webhook secret not set - webhook verification disabled")
        STRIPE_AVAILABLE = True
    except ImportError:
        logger.warning("Stripe module not installed. Payment features disabled.")
        STRIPE_AVAILABLE = False

# AI: key from env only, never in code
try:
    import openai

    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

# Flexible LLM Configuration (OpenAI, Qwen, LocalAI, etc.)
LLM_API_KEY = os.environ.get("LLM_API_KEY") or os.environ.get("OPENAI_API_KEY") or os.environ.get("OPEN_AI_KEY", "").strip()
LLM_BASE_URL = os.environ.get("LLM_BASE_URL")  # e.g. https://dashscope.aliyuncs.com/compatible-mode/v1
LLM_MODEL = os.environ.get("LLM_MODEL") or os.environ.get("OPENAI_CHAT_MODEL", "gpt-4o-mini")

AI_CHAT_ENABLED = OPENAI_AVAILABLE and bool(LLM_API_KEY)

if OPENAI_AVAILABLE and not LLM_API_KEY:
    logger.info("LLM_API_KEY not set; AI chat disabled")


# -------------------------------------------------------------------
# Validation Utilities for API Robustness
# -------------------------------------------------------------------
def validate_game_id(game_id: str) -> str:
    """Validate and normalize game ID."""
    if not game_id or not isinstance(game_id, str):
        raise ValueError("Game ID is required and must be a string")

    game_id = game_id.strip().lower()
    allowed_games = {g["id"] for g in SUPPORTED_GAMES}

    if game_id not in allowed_games:
        raise ValueError(f"Invalid game ID. Must be one of: {', '.join(sorted(allowed_games))}")

    return game_id


def validate_limit(limit: str, default: int = 10, max_allowed: int = 50) -> int:
    """Validate and sanitize limit parameter."""
    try:
        if limit is None:
            return default
        limit_int = int(limit)
        if limit_int < 1:
            return 1
        if limit_int > max_allowed:
            return max_allowed
        return limit_int
    except (TypeError, ValueError):
        return default


def validate_search_query(query: str) -> str:
    """Validate and sanitize search query."""
    if not query:
        raise ValueError("Search query is required")

    query = str(query).strip()
    if len(query) < 1:
        raise ValueError("Search query must be at least 1 character")
    if len(query) > 200:
        raise ValueError("Search query too long (max 200 characters)")

    # Remove potentially harmful characters
    query = re.sub(r'[<>"\']', "", query)
    return query


def validate_mod_list(mod_list: str) -> str:
    """Validate mod list input."""
    if not mod_list:
        raise ValueError("Mod list is required")

    mod_list = str(mod_list).strip()
    if len(mod_list) > 100000:  # 100KB limit
        raise ValueError("Mod list too large (max 100KB)")

    return mod_list


def validate_email(email: str) -> str:
    """Basic email validation."""
    if not email:
        raise ValueError("Email is required")

    email = str(email).strip().lower()
    if not re.match(r"^[^@]+@[^@]+\.[^@]+$", email):
        raise ValueError("Invalid email format")

    return email


def validate_list_name(name: str) -> str:
    """Validate saved list name."""
    if not name:
        raise ValueError("List name is required")

    name = str(name).strip()
    if len(name) < 1:
        raise ValueError("List name cannot be empty")
    if len(name) > 100:
        raise ValueError("List name too long (max 100 characters)")

    # Remove potentially harmful characters
    name = re.sub(r'[<>"\']', "", name)
    return name


def api_error(message: str, status_code: int = 400, details: dict = None):
    """Standardized API error response."""
    response = {
        "success": False,
        "error": message,
        "timestamp": datetime.utcnow().isoformat(),
    }
    if details:
        response["details"] = details
    return jsonify(response), status_code


def api_success(data: dict = None, message: str = None):
    """Standardized API success response."""
    response = {
        "success": True,
        "timestamp": datetime.utcnow().isoformat(),
    }
    if data:
        response.update(data)
    if message:
        response["message"] = message
    return jsonify(response)


app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)  # Trust reverse proxy headers

# Gzip compression for faster responses (2025 best practice)
try:
    from flask_compress import Compress

    Compress(app)
except ImportError:
    pass  # Graceful fallback if Flask-Compress not installed

# Security settings
app.config.update(
    SECRET_KEY=config.SECRET_KEY,
    SESSION_COOKIE_SECURE=config.SESSION_COOKIE_SECURE,
    SESSION_COOKIE_HTTPONLY=config.SESSION_COOKIE_HTTPONLY,
    SESSION_COOKIE_SAMESITE=config.SESSION_COOKIE_SAMESITE,
    PERMANENT_SESSION_LIFETIME=86400,  # 24 hours
    REMEMBER_COOKIE_DURATION=86400 * 30,  # 30 days
)

# Production-specific session configuration (fixes OAuth 500 errors)
if os.environ.get("FLASK_ENV") == "production":
    app.config["SESSION_COOKIE_SECURE"] = True
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"  # NOT 'Strict' — breaks OAuth redirects
    app.config["SESSION_COOKIE_HTTPONLY"] = True
    app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(days=30)


# Data file check on startup (Priority 4B)
@app.before_request
def check_data_ready():
    if not hasattr(app, "_data_checked"):
        app._data_checked = True
        import glob

        data_files = glob.glob("data/*_mod_database.json")
        if not data_files:
            # Trigger async data download
            import threading

            from loot_parser import bootstrap_loot_data

            t = threading.Thread(target=bootstrap_loot_data, daemon=True)
            t.start()
            app._data_loading = True
        else:
            app._data_loading = False


def get_ai_client():
    """Return configured AI client (OpenAI or compatible)."""
    return openai.OpenAI(api_key=LLM_API_KEY, base_url=LLM_BASE_URL)

# BASE_URL configuration for OAuth callbacks
BASE_URL = os.environ.get("BASE_URL", "https://skymodderai.onrender.com").rstrip("/")

# Stripe configuration (handled in config.py)
stripe_price_id = config.STRIPE_PRO_PRICE_ID or ""
stripe_openclaw_price_id = config.STRIPE_OPENCLAW_PRICE_ID or ""
stripe_webhook_secret = config.STRIPE_WEBHOOK_SECRET or ""
# Marketing revamp: Everything is free. Payments enabled for donation.
PAYMENTS_ENABLED = config.PAYMENTS_ENABLED and STRIPE_AVAILABLE

OPENCLAW_ENABLED = os.environ.get("SKYMODDERAI_OPENCLAW_ENABLED", "0").lower() in (
    "1",
    "true",
    "yes",
)
OPENCLAW_SANDBOX_ROOT = (
    os.environ.get("OPENCLAW_SANDBOX_ROOT", "").strip() or "./openclaw_workspace"
)
OPENCLAW_MAX_FILES = int(os.environ.get("OPENCLAW_MAX_FILES", "500"))
OPENCLAW_MAX_BYTES = int(os.environ.get("OPENCLAW_MAX_BYTES", str(50 * 1024 * 1024)))
OPENCLAW_MAX_PATH_DEPTH = int(os.environ.get("OPENCLAW_MAX_PATH_DEPTH", "10"))
OPENCLAW_MAX_PATH_LENGTH = int(os.environ.get("OPENCLAW_MAX_PATH_LENGTH", "220"))
OPENCLAW_REQUIRE_SAME_IP = os.environ.get("OPENCLAW_REQUIRE_SAME_IP", "1").lower() in (
    "1",
    "true",
    "yes",
)
OPENCLAW_ALLOWED_EXTENSIONS = frozenset(
    {
        ".txt",
        ".md",
        ".json",
        ".yaml",
        ".yml",
        ".ini",
        ".esp",
        ".esm",
        ".esl",
        ".psc",
        ".log",
    }
)
OPENCLAW_ALLOWED_OPERATIONS = frozenset(
    {"read", "write", "list", "delete", "move", "copy", "mkdir", "stat"}
)
OPENCLAW_DENY_SEGMENTS = frozenset(
    {
        ".git",
        ".env",
        "venv",
        ".venv",
        "__pycache__",
        "node_modules",
        "windows",
        "system32",
        "syswow64",
        "drivers",
        "registry",
        "bios",
        "efi",
        "boot",
        "proc",
        "dev",
        "etc",
        "usr",
        "var",
        "appdata",
        "programdata",
        "program files",
        "program files (x86)",
        ".ssh",
        ".gnupg",
    }
)
OFFLINE_MODE = os.environ.get(
    "SKYMODDERAI_OFFLINE_MODE", os.environ.get("MODCHECK_OFFLINE_MODE", "")
).lower() in ("1", "true", "yes")
PAID_TIERS = frozenset({"pro", "pro_plus", "claw"})

# -------------------------------------------------------------------
# Database setup (simple SQLite)
# -------------------------------------------------------------------
DB_FILE = "users.db"


def get_db():
    """Get a database connection (stored in Flask's g)."""
    if "db" not in g:
        g.db = sqlite3.connect(DB_FILE)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(error):
    """Close the database connection at the end of the request."""
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    """Initialize the database schema."""
    with app.app_context():
        db = get_db()
        db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                email TEXT PRIMARY KEY,
                tier TEXT DEFAULT 'free',
                customer_id TEXT,
                subscription_id TEXT,
                email_verified INTEGER DEFAULT 0,
                password_hash TEXT,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        try:
            db.execute("ALTER TABLE users ADD COLUMN email_verified INTEGER DEFAULT 0")
            db.commit()
        except sqlite3.OperationalError:
            db.rollback()
        try:
            db.execute("ALTER TABLE users ADD COLUMN password_hash TEXT")
            db.commit()
        except sqlite3.OperationalError:
            db.rollback()
        for col in ("customer_id", "subscription_id"):
            try:
                db.execute(f"ALTER TABLE users ADD COLUMN {col} TEXT")
                db.commit()
            except sqlite3.OperationalError:
                db.rollback()
        db.execute("""
            CREATE TABLE IF NOT EXISTS user_sessions (
                token TEXT PRIMARY KEY,
                display_id TEXT UNIQUE NOT NULL,
                user_email TEXT NOT NULL,
                user_agent TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at INTEGER NOT NULL
            )
        """)
        try:
            db.execute("ALTER TABLE user_sessions ADD COLUMN display_id TEXT")
            db.commit()
        except sqlite3.OperationalError:
            db.rollback()
        db.execute("""
            CREATE TABLE IF NOT EXISTS api_keys (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_email TEXT NOT NULL,
                key_hash TEXT NOT NULL UNIQUE,
                key_prefix TEXT NOT NULL,
                label TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        db.execute("""
            CREATE TABLE IF NOT EXISTS community_posts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_email TEXT NOT NULL,
                content TEXT NOT NULL,
                tag TEXT DEFAULT 'general',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                moderated INTEGER DEFAULT 0
            )
        """)
        db.execute("""
            CREATE TABLE IF NOT EXISTS community_replies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                post_id INTEGER NOT NULL,
                user_email TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                moderated INTEGER DEFAULT 0,
                FOREIGN KEY (post_id) REFERENCES community_posts(id)
            )
        """)
        db.execute("""
            CREATE TABLE IF NOT EXISTS community_votes (
                post_id INTEGER NOT NULL,
                user_email TEXT NOT NULL,
                vote INTEGER NOT NULL,
                PRIMARY KEY (post_id, user_email),
                FOREIGN KEY (post_id) REFERENCES community_posts(id)
            )
        """)
        try:
            db.execute('ALTER TABLE community_posts ADD COLUMN tag TEXT DEFAULT "general"')
            db.commit()
        except sqlite3.OperationalError:
            db.rollback()
        db.execute("""
            CREATE TABLE IF NOT EXISTS user_specs (
                user_email TEXT PRIMARY KEY,
                specs_json TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        db.execute("""
            CREATE TABLE IF NOT EXISTS user_links (
                user_email TEXT PRIMARY KEY,
                nexus_profile_url TEXT,
                github_username TEXT,
                discord_handle TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        db.execute("""
            CREATE TABLE IF NOT EXISTS user_saved_lists (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_email TEXT NOT NULL,
                name TEXT NOT NULL,
                game TEXT,
                game_version TEXT,
                masterlist_version TEXT,
                tags TEXT,
                notes TEXT,
                preferences_json TEXT,
                source TEXT,
                list_text TEXT NOT NULL,
                saved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE (user_email, name)
            )
        """)
        # Add columns that might not exist yet
        for col_sql in (
            "ALTER TABLE user_saved_lists ADD COLUMN analysis_snapshot TEXT",
            "ALTER TABLE user_saved_lists ADD COLUMN game_version TEXT",
            "ALTER TABLE user_saved_lists ADD COLUMN masterlist_version TEXT",
            "ALTER TABLE user_saved_lists ADD COLUMN tags TEXT",
            "ALTER TABLE user_saved_lists ADD COLUMN notes TEXT",
            "ALTER TABLE user_saved_lists ADD COLUMN preferences_json TEXT",
            "ALTER TABLE user_saved_lists ADD COLUMN source TEXT",
            "ALTER TABLE user_saved_lists ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
        ):
            try:
                db.execute(col_sql)
                db.commit()
            except sqlite3.OperationalError:
                db.rollback()
        db.execute("""
            CREATE TABLE IF NOT EXISTS openclaw_grants (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_email TEXT NOT NULL,
                token_hash TEXT NOT NULL UNIQUE,
                workspace_rel TEXT NOT NULL,
                ip_hash TEXT,
                acknowledged_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at INTEGER NOT NULL
            )
        """)
        db.execute("""
            CREATE TABLE IF NOT EXISTS openclaw_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_email TEXT,
                event_type TEXT NOT NULL,
                operation TEXT,
                rel_path TEXT,
                allowed INTEGER DEFAULT 0,
                reasons_json TEXT,
                ip_hash TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        db.execute("""
            CREATE TABLE IF NOT EXISTS openclaw_permissions (
                user_email TEXT NOT NULL,
                scope TEXT NOT NULL,
                granted INTEGER DEFAULT 0,
                granted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (user_email, scope)
            )
        """)
        db.execute("""
            CREATE TABLE IF NOT EXISTS openclaw_plan_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_email TEXT NOT NULL,
                plan_id TEXT NOT NULL UNIQUE,
                game TEXT NOT NULL,
                objective TEXT,
                status TEXT DEFAULT 'proposed',
                plan_json TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                executed_at TIMESTAMP
            )
        """)
        db.execute("""
            CREATE TABLE IF NOT EXISTS openclaw_feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_email TEXT NOT NULL,
                game TEXT NOT NULL,
                fps_avg REAL,
                crashes INTEGER DEFAULT 0,
                stutter_events INTEGER DEFAULT 0,
                enjoyment_score INTEGER,
                notes TEXT,
                feedback_json TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        db.execute("""
            CREATE TABLE IF NOT EXISTS user_feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_email TEXT,
                type TEXT NOT NULL,
                category TEXT NOT NULL,
                content TEXT NOT NULL,
                context_json TEXT,
                status TEXT DEFAULT 'open',
                priority INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                resolved_at TIMESTAMP
            )
        """)
        db.execute("""
            CREATE TABLE IF NOT EXISTS user_activity (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_email TEXT,
                event_type TEXT NOT NULL,
                event_data TEXT,
                session_id TEXT,
                ip_hash TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        db.execute("""
            CREATE TABLE IF NOT EXISTS satisfaction_surveys (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_email TEXT,
                rating INTEGER NOT NULL,
                feedback_text TEXT,
                context_json TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        db.execute("""
            CREATE TABLE IF NOT EXISTS community_reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                post_id INTEGER,
                reply_id INTEGER,
                reporter_email TEXT,
                reason TEXT NOT NULL,
                details TEXT,
                status TEXT DEFAULT 'open',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        db.execute("""
            CREATE TABLE IF NOT EXISTS conflict_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                game TEXT,
                mod_a TEXT,
                mod_b TEXT,
                conflict_type TEXT,
                last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                occurrence_count INTEGER DEFAULT 1,
                UNIQUE(game, mod_a, mod_b, conflict_type)
            )
        """)
        db.commit()


# Initialize on startup
init_db()

# Session cookie name and lifetimes (seconds)
SESSION_COOKIE_NAME = "session_token"
SESSION_SHORT_LIFETIME = 86400  # 24 hours
SESSION_LONG_LIFETIME = 30 * 86400  # 30 days (remember me)

# Environment detection
_in_production = os.getenv("FLASK_ENV") == "production"

# OAuth configuration
GOOGLE_OAUTH_ENABLED = config.GOOGLE_OAUTH_ENABLED
GITHUB_OAUTH_ENABLED = config.GITHUB_OAUTH_ENABLED


# Import OAuth functions after app is created to avoid circular imports
def init_oauth_routes():
    from oauth_utils import (
        github_oauth_authorize,
        github_oauth_callback,
        google_oauth_authorize,
        google_oauth_callback,
    )

    # Register OAuth routes
    app.route("/auth/google")(google_oauth_authorize)
    app.route("/auth/google/callback")(google_oauth_callback)
    app.route("/auth/github")(github_oauth_authorize)
    app.route("/auth/github/callback")(github_oauth_callback)


# -------------------------------------------------------------------
# LOOT parser(s) - default game preloaded, others lazy-loaded
# -------------------------------------------------------------------
DEFAULT_GAME = "skyrimse"
SUPPORTED_GAMES = [
    {"id": "skyrimse", "name": "Skyrim SE (2016 Remaster)", "nexus_slug": "skyrimspecialedition"},
    {"id": "skyrim", "name": "Skyrim LE (2011 Original)", "nexus_slug": "skyrim"},
    {"id": "skyrimvr", "name": "Skyrim VR", "nexus_slug": "skyrimspecialedition"},
    {"id": "oblivion", "name": "Oblivion", "nexus_slug": "oblivion"},
    {"id": "fallout3", "name": "Fallout 3", "nexus_slug": "fallout3"},
    {"id": "falloutnv", "name": "Fallout: New Vegas", "nexus_slug": "newvegas"},
    {"id": "fallout4", "name": "Fallout 4", "nexus_slug": "fallout4"},
    {"id": "starfield", "name": "Starfield", "nexus_slug": "starfield"},
]
NEXUS_GAME_SLUGS = {g["id"]: g["nexus_slug"] for g in SUPPORTED_GAMES}
GAME_DISPLAY_NAMES = {g["id"]: g["name"] for g in SUPPORTED_GAMES}
MAX_PARSER_CACHE = 8
_parsers = OrderedDict()  # key: (game, version), value: LOOTParser


def _extract_things_to_verify(conflicts_list) -> list:
    """From conflict messages, extract short 'things to check on your PC' items (game/SKSE/version). We can't run a PC diagnostic—this lists what the masterlist says to verify."""
    seen = set()
    out = []
    raw = []
    for c in conflicts_list:
        msg = getattr(c, "message", None) or ""
        raw.append(msg)
    text = " ".join(raw).lower()
    checks = [
        ("Requires SKSE", "skse"),
        ("Requires Skyrim", "game version (Skyrim)"),
        ("Requires version", "game or mod version"),
        ("not compatible with your version", "game/mod version match"),
        ("product_version", "game executable version"),
        ("ENBSeries", "ENB version"),
    ]
    for phrase, label in checks:
        if phrase.lower() in text and label not in seen:
            seen.add(label)
            out.append(label)
    return out


def get_parser(game: str, version: str = "latest"):
    """Get or create LOOT parser for the given game and masterlist version. Loads from JSON cache first for fast startup."""
    game = (game or DEFAULT_GAME).lower()
    if game not in {g["id"] for g in SUPPORTED_GAMES}:
        game = DEFAULT_GAME
    version_key = version.lower() if version and version != "latest" else "latest"
    key = (game, version_key)
    if key in _parsers:
        _parsers.move_to_end(key)
        return _parsers[key]

    p = LOOTParser(game, version=version)
    # JSON cache first (fast path when data exists)
    if p.load_database():
        logger.info(f"Loaded {game} from cache ({len(p.mod_database)} mods)")
    elif p.download_masterlist(force_refresh=False):
        p.parse_masterlist()
        p.save_database()
    else:
        if version_key != "latest":
            return get_parser(game, "latest")
        logger.warning(f"No masterlist for {game}, using {DEFAULT_GAME}")
        return get_parser(DEFAULT_GAME, version)

    _parsers[key] = p
    _parsers.move_to_end(key)
    while len(_parsers) > MAX_PARSER_CACHE:
        evicted_key, _ = _parsers.popitem(last=False)
        logger.info("Evicted parser cache entry: %s:%s", evicted_key[0], evicted_key[1])
    return _parsers[key]


# Preload default game so app starts with working data
parser = get_parser(DEFAULT_GAME)
logger.info(f"LOOT masterlist loaded for {DEFAULT_GAME} ({len(parser.mod_database)} mods)")

# Game-specific sample mod lists: typical base + DLC + "what people download first", with some that may conflict to show utility
SAMPLE_MOD_LISTS = {
    "skyrimse": """*Skyrim.esm
*Update.esm
*Dawnguard.esm
*HearthFires.esm
*Dragonborn.esm
*Unofficial Skyrim Special Edition Patch.esp
*Falskaar.esm
*LegacyoftheDragonborn.esm
*BSAssets.esm
*BSHeartland.esm
*BS_DLC_patch.esp
*SkyUI_SE.esp
*Alternate Start - Live Another Life.esp
*Ordinator - Perks of Skyrim.esp
*Immersive Citizens - AI Overhaul.esp
*Relationship Dialogue Overhaul.esp
*Cutting Room Floor.esp
*Open Cities Skyrim.esp""",
    "skyrim": """*Skyrim.esm
*Update.esm
*Dawnguard.esm
*HearthFires.esm
*Dragonborn.esm
*Unofficial Skyrim Legendary Edition Patch.esp
*SkyUI.esp
*Alternate Start - Live Another Life.esp
*Ordinator - Perks of Skyrim.esp
*Immersive Citizens - AI Overhaul.esp""",
    "skyrimvr": """*Skyrim.esm
*Update.esm
*Dawnguard.esm
*HearthFires.esm
*Dragonborn.esm
*Unofficial Skyrim Special Edition Patch.esp
*SkyUI_SE.esp
*VRIK Player Avatar.esp
*Spell Wheel VR.esp
*Alternate Start - Live Another Life.esp""",
    "oblivion": """*Oblivion.esm
*DLCShiveringIsles.esp
*DLCBattlehornCastle.esp
*DLCFrostcrag.esp
*DLCMehrunesRazor.esp
*DLCSpellTomes.esp
*DLCThievesDen.esp
*DLCVileLair.esp
*Knights.esp
*Unofficial Oblivion Patch.esp
*Unofficial Shivering Isles Patch.esp
*DLCHorseArmor - Unofficial Patch.esp""",
    "fallout3": """*Fallout3.esm
*Anchorage.esm
*ThePitt.esm
*BrokenSteel.esm
*PointLookout.esm
*Zeta.esm
*Unofficial Fallout 3 Patch.esp
*Fallout3 - Project Beauty.esp
*EVE.esp""",
    "falloutnv": """*FalloutNV.esm
*DeadMoney.esm
*HonestHearts.esm
*OldWorldBlues.esm
*LonesomeRoad.esm
*GunRunnersArsenal.esm
*ClassicPack.esm
*MercenaryPack.esm
*TribalPack.esm
*CaravanPack.esm
*YUP - Base Game and All DLC.esp
*NVAC - New Vegas Anti Crash.esp
*The Mod Configuration Menu.esp
*JSawyer.esp
*Weapon Mods Expanded.esp""",
    "fallout4": """*Fallout4.esm
*DLCRobot.esm
*DLCworkshop01.esm
*DLCCoast.esm
*DLCworkshop02.esm
*DLCworkshop03.esm
*DLCNukaWorld.esm
*Unofficial Fallout 4 Patch.esp
*ArmorKeywords.esm
*SimSettlements.esm
*WorkshopFramework.esm
*TrueStormsFO4.esp
*Better Settlers.esp
*Start Me Up.esp""",
    "starfield": """*Starfield.esm
*Constellation.esm
*OldMars.esm
*ShatteredSpace.esm
*StarfieldCommunityPatch.esm
*BlueprintShips-Starfield.esm
*MoreDramaticGravJumps.esp""",
}


# -------------------------------------------------------------------
# Helper functions
# -------------------------------------------------------------------
def get_user_tier(email):
    """Retrieve user tier from database."""
    if not email:
        return "free"
    # Dev/testing: treat logged-in user as Pro with full features including AI (only when not in production)
    if not _in_production:
        dev_pro = os.environ.get(
            "SKYMODDERAI_DEV_PRO", os.environ.get("MODCHECK_DEV_PRO", "")
        ).lower() in ("1", "true", "yes")
        dev_pro_plus = os.environ.get(
            "SKYMODDERAI_DEV_PRO_PLUS", os.environ.get("MODCHECK_DEV_PRO_PLUS", "")
        ).lower() in ("1", "true", "yes")
        dev_openclaw = os.environ.get(
            "SKYMODDERAI_DEV_OPENCLAW", os.environ.get("MODCHECK_DEV_OPENCLAW", "")
        ).lower() in ("1", "true", "yes")
        test_email = (
            os.environ.get(
                "SKYMODDERAI_TEST_PRO_EMAIL", os.environ.get("MODCHECK_TEST_PRO_EMAIL", "")
            )
            .strip()
            .lower()
        )
        test_openclaw_email = (
            os.environ.get(
                "SKYMODDERAI_TEST_OPENCLAW_EMAIL",
                os.environ.get("MODCHECK_TEST_OPENCLAW_EMAIL", ""),
            )
            .strip()
            .lower()
        )
        if dev_openclaw or (test_openclaw_email and email.lower() == test_openclaw_email):
            return "claw"
        if dev_pro or dev_pro_plus or (test_email and email.lower() == test_email):
            return "pro"
    try:
        db = get_db()
        row = db.execute("SELECT tier FROM users WHERE email = ?", (email.lower(),)).fetchone()
        return row["tier"] if row else "free"
    except Exception as e:
        logger.error(f"Database error in get_user_tier: {e}")
        return "free"  # Fail safe


def set_user_tier(email, tier, customer_id=None, subscription_id=None):
    """Update or insert user tier information. Preserves email_verified when updating."""
    try:
        db = get_db()
        email = email.lower()
        db.execute(
            """
            UPDATE users SET tier = ?, customer_id = ?, subscription_id = ?, last_updated = CURRENT_TIMESTAMP
            WHERE email = ?
        """,
            (tier, customer_id, subscription_id, email),
        )
        if db.total_changes == 0:
            db.execute(
                """
                INSERT INTO users (email, tier, customer_id, subscription_id, email_verified, last_updated)
                VALUES (?, ?, ?, ?, 1, CURRENT_TIMESTAMP)
            """,
                (email, tier, customer_id, subscription_id),
            )
        db.commit()
        logger.info(f"Updated user {_redact_email(email)} to tier {tier}")
    except Exception:
        logger.error(f"Failed to update user tier for {_redact_email(email)}")


def has_paid_access(tier: str) -> bool:
    """True when tier includes paid features available in Pro."""
    # Marketing revamp: Everything is free.
    return True


def is_openclaw_tier(tier: str) -> bool:
    """True when tier is OpenClaw Lab."""
    # Marketing revamp: Everything is free.
    return True


def tier_label(tier: str) -> str:
    """Human label for UI templates and confirmations."""
    return {
        "free": "Free",
        "pro": "Pro",
        "pro_plus": "Pro",
        "claw": "OpenClaw Lab",
    }.get(tier, tier)


def _tier_from_price_id(price_id: str) -> str:
    """Map Stripe price ID to internal tier."""
    if price_id and stripe_openclaw_price_id and price_id == stripe_openclaw_price_id:
        return "claw"
    if price_id and stripe_price_id and price_id == stripe_price_id:
        return "pro"
    return "pro"


def _tier_from_subscription(subscription_id: str) -> str:
    """Infer internal tier from Stripe subscription item price IDs."""
    if not subscription_id:
        return "pro"
    try:
        sub = stripe.Subscription.retrieve(subscription_id)
        items = (sub.get("items") or {}).get("data") or []
        if items:
            price_obj = items[0].get("price") or {}
            return _tier_from_price_id(price_obj.get("id") or "")
    except Exception as e:
        logger.warning("Could not infer tier from subscription %s: %s", subscription_id, e)
    return "pro"


def _tier_from_checkout_session(checkout_session) -> str:
    """Infer internal tier from checkout metadata or line item price ID."""
    metadata = checkout_session.get("metadata") or {}
    if metadata.get("target_tier") in ("pro", "claw"):
        return metadata.get("target_tier")
    try:
        line_items = stripe.checkout.Session.list_line_items(checkout_session.id, limit=1)
        if line_items and line_items.data:
            price_obj = line_items.data[0].get("price") or {}
            return _tier_from_price_id(price_obj.get("id") or "")
    except Exception as e:
        logger.warning("Could not infer tier from checkout session %s: %s", checkout_session.id, e)
    return "pro"


def get_user_specs(email):
    """Get user system specs (JSON dict) or None."""
    if not email:
        return None
    try:
        row = (
            get_db()
            .execute("SELECT specs_json FROM user_specs WHERE user_email = ?", (email.lower(),))
            .fetchone()
        )
        if row and row["specs_json"]:
            return json.loads(row["specs_json"])
        return None
    except Exception as e:
        logger.warning(f"get_user_specs: {e}")
        return None


def set_user_specs(email, specs: dict):
    """Save user system specs. specs: {cpu, gpu, ram_gb, vram_gb, resolution, storage_type, ...}."""
    if not email:
        return
    try:
        db = get_db()
        db.execute(
            """
            INSERT INTO user_specs (user_email, specs_json, updated_at)
            VALUES (?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(user_email) DO UPDATE SET specs_json = excluded.specs_json, updated_at = CURRENT_TIMESTAMP
        """,
            (email.lower(), json.dumps(specs)),
        )
        db.commit()
    except Exception as e:
        logger.warning(f"set_user_specs: {e}")


def list_user_saved_lists(
    email: str,
    game: Optional[str] = None,
    game_version: Optional[str] = None,
    masterlist_version: Optional[str] = None,
):
    """Return a list of saved list records for a user (new API)."""
    if not email:
        return []
    try:
        sql = (
            "SELECT id, name, game, game_version, masterlist_version, tags, notes, preferences_json, source, list_text, analysis_snapshot, saved_at, updated_at "
            "FROM user_saved_lists WHERE user_email = ?"
        )
        params = [email.lower()]
        if game:
            sql += " AND game = ?"
            params.append(game.strip().lower())
        if game_version:
            sql += " AND game_version = ?"
            params.append(game_version.strip())
        if masterlist_version:
            sql += " AND masterlist_version = ?"
            params.append(masterlist_version.strip())
        sql += " ORDER BY COALESCE(updated_at, saved_at) DESC, saved_at DESC"
        rows = get_db().execute(sql, params).fetchall()
        out = []
        for r in rows or []:
            prefs = None
            try:
                prefs = json.loads(r["preferences_json"]) if r["preferences_json"] else None
            except Exception:
                prefs = None

            analysis = None
            try:
                analysis = json.loads(r["analysis_snapshot"]) if r["analysis_snapshot"] else None
            except Exception:
                analysis = None

            out.append(
                {
                    "id": r["id"],
                    "name": r["name"],
                    "game": r["game"] or "",
                    "game_version": r["game_version"] or "",
                    "masterlist_version": r["masterlist_version"] or "",
                    "tags": r["tags"] or "",
                    "notes": r["notes"] or "",
                    "preferences": prefs,
                    "source": r["source"] or "",
                    "list": r["list_text"] or "",
                    "analysis_snapshot": analysis,
                    "savedAt": r["saved_at"],
                    "updatedAt": r["updated_at"] or r["saved_at"],
                }
            )
        return out
    except Exception as e:
        logger.warning(f"list_user_saved_lists: {e}")
        return []


def list_user_saved_lists_legacy_map(email: str):
    """Return legacy dict keyed by name (for backwards compatibility with older UI)."""
    items = list_user_saved_lists(email)
    out = {}
    for it in items:
        out[it["name"]] = {
            "name": it["name"],
            "game": it.get("game") or "",
            "list": it.get("list") or "",
            "savedAt": it.get("updatedAt") or it.get("savedAt"),
        }
    return out


def upsert_user_saved_list(
    email: str,
    name: str,
    game: str,
    list_text: str,
    *,
    game_version: Optional[str] = None,
    masterlist_version: Optional[str] = None,
    tags: Optional[str] = None,
    notes: Optional[str] = None,
    preferences: Optional[dict] = None,
    source: Optional[str] = None,
    analysis_snapshot: Optional[dict] = None,
):
    """Create or update a saved list for a user."""
    if not email:
        return False
    name = (name or "").strip()
    if not name:
        return False
    try:
        db = get_db()
        preferences_json = None
        if isinstance(preferences, dict):
            try:
                preferences_json = json.dumps(preferences)
            except Exception:
                preferences_json = None

        analysis_json = None
        if isinstance(analysis_snapshot, dict):
            try:
                analysis_json = json.dumps(analysis_snapshot)
            except Exception:
                analysis_json = None

        db.execute(
            """
            INSERT INTO user_saved_lists (
                user_email, name, game, game_version, masterlist_version, tags, notes, preferences_json, source, list_text, analysis_snapshot, saved_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            ON CONFLICT(user_email, name) DO UPDATE SET
                game = excluded.game,
                game_version = excluded.game_version,
                masterlist_version = excluded.masterlist_version,
                tags = excluded.tags,
                notes = excluded.notes,
                preferences_json = excluded.preferences_json,
                source = excluded.source,
                list_text = excluded.list_text,
                analysis_snapshot = excluded.analysis_snapshot,
                updated_at = CURRENT_TIMESTAMP
        """,
            (
                email.lower(),
                name,
                game,
                game_version,
                masterlist_version,
                tags,
                notes,
                preferences_json,
                source,
                list_text,
                analysis_json,
            ),
        )
        db.commit()
        return True
    except Exception as e:
        logger.warning(f"upsert_user_saved_list: {e}")
        return False


def delete_user_saved_list(
    email: str, name: Optional[str] = None, list_id: Optional[int] = None
) -> bool:
    """Delete a saved list by id (preferred) or by name for a user."""
    if not email:
        return False
    if list_id is None:
        name = (name or "").strip()
        if not name:
            return False
    if list_id is not None and int(list_id) <= 0:
        return False
    try:
        db = get_db()
        if list_id is not None:
            db.execute(
                "DELETE FROM user_saved_lists WHERE user_email = ? AND id = ?",
                (email.lower(), int(list_id)),
            )
        else:
            db.execute(
                "DELETE FROM user_saved_lists WHERE user_email = ? AND name = ?",
                (email.lower(), name),
            )
        db.commit()
        return True
    except Exception as e:
        logger.warning(f"delete_user_saved_list: {e}")
        return False


def get_user_links(email):
    """Get linked account/profile metadata for a user."""
    if not email:
        return {}
    try:
        row = (
            get_db()
            .execute(
                "SELECT nexus_profile_url, github_username, discord_handle FROM user_links WHERE user_email = ?",
                (email.lower(),),
            )
            .fetchone()
        )
        if not row:
            return {}
        return {
            "nexus_profile_url": row["nexus_profile_url"] or "",
            "github_username": row["github_username"] or "",
            "discord_handle": row["discord_handle"] or "",
        }
    except Exception as e:
        logger.warning("get_user_links: %s", e)
        return {}


def set_user_links(email, links: dict):
    """Save linked account/profile metadata for a user."""
    if not email:
        return
    nexus = (links.get("nexus_profile_url") or "").strip()[:300]
    github = (links.get("github_username") or "").strip()[:100]
    discord = (links.get("discord_handle") or "").strip()[:100]
    try:
        db = get_db()
        db.execute(
            """
            INSERT INTO user_links (user_email, nexus_profile_url, github_username, discord_handle, updated_at)
            VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(user_email) DO UPDATE SET
                nexus_profile_url = excluded.nexus_profile_url,
                github_username = excluded.github_username,
                discord_handle = excluded.discord_handle,
                updated_at = CURRENT_TIMESTAMP
        """,
            (email.lower(), nexus, github, discord),
        )
        db.commit()
    except Exception as e:
        logger.warning("set_user_links: %s", e)


def _request_ip_hash() -> str:
    """Hash request IP for privacy-safe coarse analytics."""
    ip = (
        request.headers.get("X-Forwarded-For", request.remote_addr or "unknown")
        .split(",")[0]
        .strip()
    )
    return hashlib.sha256(ip.encode("utf-8")).hexdigest()[:16]


def _request_session_fingerprint() -> str:
    """Derive a stable short session fingerprint without PII."""
    token = request.cookies.get(SESSION_COOKIE_NAME) or request.headers.get("X-Session-Id") or ""
    ua = request.headers.get("User-Agent") or ""
    raw = f"{token}:{ua}"[:400]
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:20]


def track_activity(event_type: str, event_data=None, user_email=None):
    """Persist lightweight activity events for product/community metrics."""
    try:
        db = get_db()
        payload = json.dumps(event_data or {}, ensure_ascii=True)[:2000]
        db.execute(
            """
            INSERT INTO user_activity (user_email, event_type, event_data, session_id, ip_hash)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                (user_email or session.get("user_email") or "").lower() or None,
                (event_type or "unknown").strip()[:64],
                payload,
                _request_session_fingerprint(),
                _request_ip_hash(),
            ),
        )
        db.commit()
    except Exception as e:
        logger.debug("track_activity failed: %s", e)


def parse_steam_system_info(text: str) -> dict:
    """Parse Steam Help → System Information paste. Returns dict with cpu, gpu, ram_gb, etc."""
    if not text or not isinstance(text, str):
        return {}
    out = {}
    lines = text.strip().split("\n")
    for line in lines:
        line = line.strip()
        if ":" not in line:
            continue
        k, v = line.split(":", 1)
        k, v = k.strip().lower(), v.strip()
        if not v:
            continue
        if "cpu brand" in k:
            out["cpu"] = v
        elif "processor" in k and "cpu" not in out:
            out["cpu"] = v
        elif "video card" in k:
            out["gpu"] = v
        elif k == "driver" and "gpu" not in out:
            out["gpu"] = v
        elif "chipset" in k and "gpu" not in out:
            out["gpu"] = v
        elif "memory" in k:
            try:
                import re

                match = re.search(r"(\d+)\s*(?:gb|gigabytes?|mb|megabytes?)", v, re.I)
                if match:
                    gb = int(match.group(1))
                    if "mb" in v.lower() and gb >= 1000:
                        gb = gb // 1024
                    elif gb < 4 or gb > 512:
                        continue
                    out["ram_gb"] = str(gb)
            except (ValueError, TypeError):
                pass
        elif "resolution" in k:
            out["resolution"] = v
    return out


def ensure_user_unverified(email, password=None):
    """Create user record with email_verified=0 for signup flow. Optionally set password. Idempotent."""
    try:
        db = get_db()
        email = email.lower()
        pwhash = generate_password_hash(password, method="pbkdf2:sha256") if password else None
        db.execute(
            """
            INSERT OR IGNORE INTO users (email, tier, customer_id, subscription_id, email_verified, password_hash, last_updated)
            VALUES (?, 'free', NULL, NULL, 0, ?, CURRENT_TIMESTAMP)
        """,
            (email, pwhash),
        )
        if password and db.total_changes == 0:
            db.execute(
                "UPDATE users SET password_hash = ?, last_updated = CURRENT_TIMESTAMP WHERE email = ?",
                (pwhash, email),
            )
        db.commit()
    except Exception as e:
        logger.error(f"ensure_user_unverified: {e}")


def set_user_verified(email):
    """Mark user as email-verified after they click the link."""
    try:
        db = get_db()
        db.execute("UPDATE users SET email_verified = 1 WHERE email = ?", (email.lower(),))
        db.commit()
    except Exception as e:
        logger.error(f"set_user_verified: {e}")


def is_user_verified(email):
    """Return True if user has verified their email."""
    if not email:
        return False
    try:
        db = get_db()
        row = db.execute(
            "SELECT email_verified FROM users WHERE email = ?", (email.lower(),)
        ).fetchone()
        return bool(row and row[0])
    except Exception:
        return False


def get_user_row(email):
    """Return the user row (with password_hash, customer_id, subscription_id) or None."""
    if not email:
        return None
    try:
        db = get_db()
        return db.execute(
            "SELECT email, tier, email_verified, password_hash, customer_id, subscription_id FROM users WHERE email = ?",
            (email.lower(),),
        ).fetchone()
    except Exception:
        return None


def _utc_ts():
    return int((datetime.utcnow() - datetime(1970, 1, 1)).total_seconds())


def session_create(user_email, remember_me=False, user_agent=None):
    """Create a session row and return (token, max_age)."""
    token = secrets.token_urlsafe(32)
    display_id = secrets.token_urlsafe(8)
    max_age = SESSION_LONG_LIFETIME if remember_me else SESSION_SHORT_LIFETIME
    expires_ts = _utc_ts() + max_age
    try:
        db = get_db()
        db.execute(
            "INSERT INTO user_sessions (token, display_id, user_email, user_agent, last_seen, expires_at) VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP, ?)",
            (token, display_id, user_email.lower(), (user_agent or "")[:512], expires_ts),
        )
        db.commit()
        return token, max_age
    except Exception as e:
        logger.error(f"session_create: {e}")
        return None, max_age


def session_get(token):
    """Return session row (with user_email) if token valid and not expired; else None. Updates last_seen."""
    if not token:
        return None
    try:
        db = get_db()
        now_ts = _utc_ts()
        row = db.execute(
            "SELECT token, user_email, user_agent, created_at, last_seen, expires_at FROM user_sessions WHERE token = ?",
            (token,),
        ).fetchone()
        if not row or (row["expires_at"] or 0) < now_ts:
            return None
        db.execute(
            "UPDATE user_sessions SET last_seen = CURRENT_TIMESTAMP WHERE token = ?", (token,)
        )
        db.commit()
        return row
    except Exception as e:
        logger.error(f"session_get: {e}")
        return None


def session_revoke(token):
    """Delete one session by token."""
    try:
        db = get_db()
        db.execute("DELETE FROM user_sessions WHERE token = ?", (token,))
        db.commit()
    except Exception as e:
        logger.error(f"session_revoke: {e}")


def session_revoke_all_other(user_email, keep_token):
    """Revoke all sessions for user except keep_token."""
    if not keep_token:
        return
    try:
        db = get_db()
        db.execute(
            "DELETE FROM user_sessions WHERE user_email = ? AND token != ?",
            (user_email.lower(), keep_token),
        )
        db.commit()
    except Exception as e:
        logger.error(f"session_revoke_all_other: {e}")


def session_list(user_email, current_token=None):
    """List all sessions for user; each dict has display_id, user_agent, created_at, last_seen, current (bool). Backfills display_id if missing."""
    try:
        db = get_db()
        rows = db.execute(
            "SELECT token, display_id, user_agent, created_at, last_seen FROM user_sessions WHERE user_email = ? AND expires_at > ? ORDER BY last_seen DESC",
            (user_email.lower(), _utc_ts()),
        ).fetchall()
        out = []
        for r in rows:
            display_id = r["display_id"]
            if not display_id:
                display_id = secrets.token_urlsafe(8)
                db.execute(
                    "UPDATE user_sessions SET display_id = ? WHERE token = ?",
                    (display_id, r["token"]),
                )
                db.commit()
            out.append(
                {
                    "display_id": display_id,
                    "user_agent": r["user_agent"] or "Unknown device",
                    "created_at": r["created_at"],
                    "last_seen": r["last_seen"],
                    "current": r["token"] == current_token if current_token else False,
                }
            )
        return out
    except Exception as e:
        logger.error(f"session_list: {e}")
        return []


def session_revoke_by_display_id(user_email, display_id):
    """Revoke one session by display_id if it belongs to user. Returns True if revoked."""
    if not display_id or not user_email:
        return False
    try:
        db = get_db()
        db.execute(
            "DELETE FROM user_sessions WHERE user_email = ? AND display_id = ?",
            (user_email.lower(), display_id),
        )
        db.commit()
        return db.total_changes > 0
    except Exception as e:
        logger.error(f"session_revoke_by_display_id: {e}")
        return False


# -------------------------------------------------------------------
# Developer API keys (link public key / API key for engine access)
# -------------------------------------------------------------------
API_KEY_PREFIX = "mck_"


def _hash_api_key(key):
    return hashlib.sha256(key.encode("utf-8")).hexdigest()


def api_key_create(user_email, label=None):
    """Create a new API key. Returns (raw_key, key_id, prefix, label, created_at) or (None, ...) on failure. Caller must show raw_key only once."""
    raw = API_KEY_PREFIX + secrets.token_urlsafe(32)
    key_hash = _hash_api_key(raw)
    prefix = raw[:12] + "..."  # e.g. mck_abc12...
    try:
        db = get_db()
        db.execute(
            "INSERT INTO api_keys (user_email, key_hash, key_prefix, label) VALUES (?, ?, ?, ?)",
            (user_email.lower(), key_hash, prefix, (label or "").strip()[:64] or None),
        )
        db.commit()
        row = db.execute(
            "SELECT id, created_at FROM api_keys WHERE key_hash = ?", (key_hash,)
        ).fetchone()
        return (raw, row["id"], prefix, label or "", row["created_at"])
    except Exception as e:
        logger.error(f"api_key_create: {e}")
        return (None, None, None, None, None)


def api_key_lookup(raw_key):
    """Return user_email for a valid API key, else None."""
    if not raw_key or not raw_key.startswith(API_KEY_PREFIX):
        return None
    key_hash = _hash_api_key(raw_key)
    try:
        row = (
            get_db()
            .execute("SELECT user_email FROM api_keys WHERE key_hash = ?", (key_hash,))
            .fetchone()
        )
        return row["user_email"] if row else None
    except Exception:
        return None


def api_key_list(user_email):
    """List API keys for user (id, key_prefix, label, created_at) — no raw keys."""
    try:
        db = get_db()
        rows = db.execute(
            "SELECT id, key_prefix, label, created_at FROM api_keys WHERE user_email = ? ORDER BY created_at DESC",
            (user_email.lower(),),
        ).fetchall()
        return [dict(r) for r in rows]
    except Exception as e:
        logger.error(f"api_key_list: {e}")
        return []


def api_key_revoke(user_email, key_id):
    """Revoke (delete) an API key if it belongs to user. Returns True if deleted."""
    try:
        db = get_db()
        db.execute(
            "DELETE FROM api_keys WHERE id = ? AND user_email = ?",
            (int(key_id), user_email.lower()),
        )
        db.commit()
        return db.total_changes > 0
    except Exception as e:
        logger.error(f"api_key_revoke: {e}")
        return False


def send_verification_email(to_email, verify_url):
    """Send a single verification email. Uses env: MAIL_FROM, MAIL_HOST, MAIL_PORT, MAIL_USER, MAIL_PASSWORD, MAIL_USE_SSL."""
    from_addr = config.MAIL_DEFAULT_SENDER
    host = config.MAIL_SERVER
    port = int(config.MAIL_PORT or 0)
    user = config.MAIL_USERNAME
    password = config.MAIL_PASSWORD
    use_ssl = config.MAIL_USE_TLS
    if not host or not port:
        logger.warning(
            "MAIL_HOST/MAIL_PORT not set; verification link generated (not sent). "
            "Set MAIL_* env vars to send real emails. Dev fallback: %s",
            verify_url[:80] + "..." if len(verify_url) > 80 else verify_url,
        )
        return
    msg = MIMEMultipart("alternative")
    msg["Subject"] = "Verify your SkyModderAI email"
    msg["From"] = from_addr
    msg["To"] = to_email
    text = f"""You're signing up for SkyModderAI. Click the link below to verify your email—then you can log in and, if you want, go to Pro checkout.\n\n{verify_url}\n\nIf you didn't request this, you can ignore this email."""
    msg.attach(MIMEText(text, "plain"))
    try:
        if use_ssl or port == 465:
            with smtplib.SMTP_SSL(host, port) as s:
                if user and password:
                    s.login(user, password)
                s.sendmail(from_addr, [to_email], msg.as_string())
        else:
            with smtplib.SMTP(host, port) as s:
                if user and password:
                    s.starttls()
                    s.login(user, password)
                s.sendmail(from_addr, [to_email], msg.as_string())
        logger.info(f"Verification email sent to {_redact_email(to_email)}")
    except Exception as e:
        logger.exception("Failed to send verification email: %s", e)


def make_verification_token(email):
    """Generate a signed token for email verification. Expires in 24 hours."""
    s = URLSafeTimedSerializer(app.config["SECRET_KEY"], salt="verify-email")
    return s.dumps(email.lower())


def verify_token(token):
    """Return email from token or None if invalid/expired."""
    s = URLSafeTimedSerializer(app.config["SECRET_KEY"], salt="verify-email")
    try:
        return s.loads(token, max_age=86400)
    except Exception:
        return None


def login_required(f):
    """Decorator to require login for routes (redirects to login page)."""

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_email" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)

    return decorated_function


def login_required_api(f):
    """Decorator to require login for API routes (returns 401 JSON)."""

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_email" not in session:
            return api_error("Unauthorized", 401)
        return f(*args, **kwargs)

    return decorated_function


@app.before_request
def load_session_from_cookie():
    """Resolve session_token cookie into g.user_email and session['user_email']."""
    token = request.cookies.get(SESSION_COOKIE_NAME)
    if token:
        row = session_get(token)
        if row:
            email = row["user_email"]
            g.user_email = email
            session["user_email"] = email
            session["_session_token"] = token
            return
    g.user_email = None
    session.pop("user_email", None)
    session.pop("_session_token", None)


# -------------------------------------------------------------------
# Rate limiting (in-memory, per-worker; use Redis for multi-worker prod)
# -------------------------------------------------------------------
_rate_limit_store = defaultdict(list)


def _rate_limit_key():
    return (
        request.headers.get("X-Forwarded-For", request.remote_addr or "unknown")
        .split(",")[0]
        .strip()
    )


def _check_rate_limit(limit: int, key_prefix: str = "default") -> bool:
    """Return True if under limit, False if rate limited."""
    if not _in_production:
        return True
    key = f"{key_prefix}:{_rate_limit_key()}"
    now = _time()
    window_start = now - RATE_LIMIT_WINDOW
    store = _rate_limit_store[key]
    store[:] = [t for t in store if t > window_start]
    if len(store) >= limit:
        return False
    store.append(now)
    return True


def rate_limit(limit: int, key_prefix: str = "api"):
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            if not _check_rate_limit(limit, key_prefix):
                return api_error("Too many requests. Please slow down.", 429)
            return f(*args, **kwargs)

        return wrapped

    return decorator


# -------------------------------------------------------------------
# Error handlers
# -------------------------------------------------------------------
@app.after_request
def add_security_headers(response):
    """Add security headers. CSP is permissive to allow CDNs (marked, fonts)."""
    if _in_production:
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "SAMEORIGIN"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return response


@app.errorhandler(404)
def not_found(e):
    """Custom 404 page."""
    if request.path.startswith("/api/"):
        return api_error("Not found", 404)
    return render_template("error.html", code=404, message="Page not found"), 404


@app.errorhandler(500)
def server_error(e):
    """Custom 500 page."""
    logger.exception("Server error: %s", e)
    if request.path.startswith("/api/"):
        return api_error("Internal server error", 500)
    return render_template(
        "error.html", code=500, message="Something went wrong. We've been notified."
    ), 500


# -------------------------------------------------------------------
# API Routes
# -------------------------------------------------------------------
@app.route("/api/game-versions")
def get_game_versions():
    """API endpoint to get game version information"""
    game = request.args.get("game", "").lower()
    game_versions_file = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "data/game_versions.json"
    )

    try:
        with open(game_versions_file, "r") as f:
            data = json.load(f)

        if game and game in data:
            return jsonify({game: data[game]})
        return jsonify(data)
    except FileNotFoundError:
        return jsonify({"error": "Game versions file not found"}), 404
    except json.JSONDecodeError:
        return jsonify({"error": "Invalid game versions file"}), 500
    except Exception as e:
        app.logger.error(f"Error in get_game_versions: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500


@app.route("/api/load-order/share", methods=["POST"])
@login_required_api
def share_load_order():
    """
    Create a shareable link for the current load order and analysis.

    Request JSON:
    {
        "game": "skyrimse",
        "game_version": "1.6.1170",
        "masterlist_version": "2025.01.15",
        "mod_list": [
            {"name": "Unofficial Patch", "version": "4.2.8"},
            ...
        ],
        "analysis_results": { ... },
        "title": "My Awesome Mod List",
        "notes": "This is a test share",
        "is_public": true
    }

    Returns: {"share_id": "abc123..."}
    """
    data = request.get_json()

    # Validate required fields
    required = ["game", "mod_list", "analysis_results"]
    if not all(field in data for field in required):
        return api_error("Missing required fields", 400)

    # Ensure mod_list is a list of dicts with at least a 'name' key
    if not isinstance(data["mod_list"], list) or not all(
        isinstance(m, dict) and "name" in m for m in data["mod_list"]
    ):
        return api_error("Invalid mod_list format", 400)

    # Generate a share ID and save to database
    share_id = secrets.token_urlsafe(9)  # ~12 chars, URL-safe
    expires_at = datetime.utcnow() + timedelta(days=30)

    try:
        db = get_db()
        db.execute(
            """
            INSERT INTO shared_load_orders (
                id, created_at, expires_at, game, game_version, masterlist_version,
                mod_list, analysis_results, user_email, title, notes, is_public
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                share_id,
                datetime.utcnow(),
                expires_at,
                data["game"],
                data.get("game_version"),
                data.get("masterlist_version"),
                json.dumps(data["mod_list"]),
                json.dumps(data["analysis_results"]),
                session.get("user_email"),
                data.get("title"),
                data.get("notes"),
                data.get("is_public", True),
            ),
        )
        db.commit()

        # Return the shareable link
        share_url = f"{config.BASE_URL}/share/{share_id}"
        return jsonify(
            {
                "share_id": share_id,
                "share_url": share_url,
                "expires_at": expires_at.isoformat() + "Z",
            }
        )

    except Exception as e:
        app.logger.error(f"Error creating shared load order: {e}", exc_info=True)
        return api_error("Failed to create share link", 500)


@app.route("/api/load-order/share/<share_id>", methods=["GET"])
def get_shared_load_order(share_id):
    """
    Retrieve a shared load order by ID.

    Returns: {
        "id": "abc123...",
        "created_at": "2025-02-17T03:30:00Z",
        "expires_at": "2025-03-19T03:30:00Z",
        "game": "skyrimse",
        "game_version": "1.6.1170",
        "masterlist_version": "2025.01.15",
        "mod_list": [...],
        "analysis_results": {...},
        "title": "My Awesome Mod List",
        "notes": "This is a test share",
        "view_count": 42,
        "is_public": true,
        "user_display": "user@example.com"  # or None if anonymous
    }
    """
    try:
        db = get_db()
        now = datetime.utcnow()

        # Get the shared load order
        row = db.execute(
            """
            UPDATE shared_load_orders
            SET view_count = view_count + 1,
                last_viewed_at = ?
            WHERE id = ? AND expires_at > ?
            RETURNING *
            """,
            (now, share_id, now),
        ).fetchone()

        if not row:
            return api_error("Share not found or expired", 404)

        # Convert to dict and parse JSON fields
        result = dict(row)
        result["mod_list"] = json.loads(result["mod_list"])
        result["analysis_results"] = json.loads(result["analysis_results"])

        # Redact user email for privacy, but show first part if public
        if result.get("user_email"):
            if result.get("is_public"):
                user, domain = result["user_email"].split("@", 1)
                result["user_display"] = f"{user[:2]}...@{domain}"
            else:
                result["user_display"] = None

        # Remove sensitive fields
        for field in ["user_email"]:
            result.pop(field, None)

        return jsonify(result)

    except Exception as e:
        app.logger.error(f"Error retrieving shared load order {share_id}: {e}", exc_info=True)
        return api_error("Failed to retrieve shared load order", 500)


@app.route("/api/load-order/shares", methods=["GET"])
@login_required_api
def list_shared_load_orders():
    """
    List all shared load orders for the current user.

    Returns: [
        {
            "id": "abc123...",
            "created_at": "2025-02-17T03:30:00Z",
            "expires_at": "2025-03-19T03:30:00Z",
            "game": "skyrimse",
            "title": "My Awesome Mod List",
            "view_count": 42,
            "is_public": true
        },
        ...
    ]
    """
    try:
        db = get_db()
        now = datetime.utcnow()

        rows = db.execute(
            """
            SELECT id, created_at, expires_at, game, title, view_count, is_public
            FROM shared_load_orders
            WHERE user_email = ? AND expires_at > ?
            ORDER BY created_at DESC
            """,
            (session["user_email"], now),
        ).fetchall()

        return jsonify([dict(row) for row in rows])

    except Exception as e:
        app.logger.error(f"Error listing shared load orders: {e}", exc_info=True)
        return api_error("Failed to list shared load orders", 500)


@app.route("/api/load-order/share/<share_id>", methods=["DELETE"])
@login_required_api
def delete_shared_load_order(share_id):
    """
    Delete a shared load order. Only the owner can delete their shares.

    Returns: 204 No Content on success
    """
    try:
        db = get_db()

        # Verify ownership
        result = db.execute(
            "DELETE FROM shared_load_orders WHERE id = ? AND user_email = ? RETURNING id",
            (share_id, session["user_email"]),
        )
        db.commit()

        if not result.fetchone():
            return api_error("Share not found or not owned by user", 404)

        return "", 204

    except Exception as e:
        app.logger.error(f"Error deleting shared load order {share_id}: {e}", exc_info=True)
        return api_error("Failed to delete shared load order", 500)


# Route to view a shared load order in the web UI
@app.route("/share/<share_id>")
def view_shared_load_order(share_id):
    """Render the shared load order in a user-friendly web page."""
    return render_template("shared_load_order.html", share_id=share_id)


# -------------------------------------------------------------------
# Routes
# -------------------------------------------------------------------
# User-facing messages for index ?error= param (payment/verification redirects)
INDEX_ERROR_MESSAGES = {
    "missing_session": "Payment session expired or invalid. Please try checkout again from your profile.",
    "payment_incomplete": "Payment was not completed. Your card was not charged. Try again when you're ready.",
    "stripe_error": "Something went wrong with payment processing. Please try again or contact support.",
    "verification_failed": "We couldn't verify your payment. Your card was not charged. Please try again or contact support.",
}


@app.route("/")
def index():
    """Main page."""
    user_email = session.get("user_email")
    user_tier = get_user_tier(user_email) if user_email else "free"
    error_param = request.args.get("error", "").strip()
    error_message = INDEX_ERROR_MESSAGES.get(error_param, "") if error_param else ""
    return render_template(
        "index.html",
        user_tier=user_tier,
        payments_enabled=PAYMENTS_ENABLED,
        error_message=error_message,
        openclaw_enabled=OPENCLAW_ENABLED,
    )


@app.route("/terms")
def terms():
    """Public terms of service page."""
    return render_template("terms.html")


@app.route("/privacy")
def privacy():
    """Public privacy policy page."""
    return render_template("privacy.html")


@app.route("/quickstart")
def quickstart_page():
    """Stable URL for indexing quickstart section."""
    return redirect("/#panel-quickstart")


@app.route("/safety")
def safety():
    """Public safety and model-constraint disclosure page."""
    return render_template("safety.html")


@app.route("/api")
def api_hub():
    """Human-readable API hub for developers and search indexing."""
    return render_template("api_hub.html")


@app.route("/auth")
def auth():
    """Combined login + signup page, side by side."""
    active = request.args.get("tab", "login")
    if active not in ("login", "signup"):
        active = "login"
    return render_template(
        "auth.html",
        google_oauth_enabled=GOOGLE_OAUTH_ENABLED,
        github_oauth_enabled=GITHUB_OAUTH_ENABLED,
        active=active,
    )


@app.route("/login")
def login():
    """Redirect to combined auth page."""
    args = dict(request.args)
    args["tab"] = "login"
    return redirect(url_for("auth", **args))


@app.route("/api/login", methods=["POST"])
def login_submit():
    """Log in with email and password; create session, set cookie, return success or 401."""
    data = request.get_json() or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""
    remember_me = bool(data.get("remember_me"))
    if not email or "@" not in email:
        return jsonify({"error": "Valid email required."}), 400
    if not password:
        return jsonify({"error": "Password required."}), 400
    row = get_user_row(email)
    if not row or not row.get("password_hash"):
        return jsonify(
            {"error": "No account with that email, or account has no password set. Sign up first."}
        ), 401
    if not check_password_hash(row["password_hash"], password):
        return jsonify({"error": "Incorrect password."}), 401
    next_param = request.args.get("next", "").strip()
    if next_param and next_param.startswith("/") and "//" not in next_param:
        next_url = next_param
    else:
        next_url = url_for("index")
    token, max_age = session_create(
        email, remember_me=remember_me, user_agent=request.headers.get("User-Agent")
    )
    resp = jsonify({"success": True, "redirect": next_url})
    if token:
        resp.set_cookie(
            SESSION_COOKIE_NAME,
            token,
            max_age=max_age,
            httponly=True,
            secure=app.config["SESSION_COOKIE_SECURE"],
            samesite=app.config["SESSION_COOKIE_SAMESITE"],
        )
    return resp


def _google_oauth_state_make(next_url=""):
    s = URLSafeTimedSerializer(app.config["SECRET_KEY"], salt="google-oauth-state")
    return s.dumps({"rnd": secrets.token_hex(16), "next": next_url[:200]})


def _google_oauth_state_verify(state):
    if not state:
        return None
    s = URLSafeTimedSerializer(app.config["SECRET_KEY"], salt="google-oauth-state")
    try:
        return s.loads(state, max_age=600)
    except Exception:
        return None


@app.route("/auth/google")
def auth_google():
    """Redirect to Google OAuth consent page."""
    from oauth_utils import google_oauth_authorize

    return google_oauth_authorize()


@app.route("/auth/google/callback")
def auth_google_callback():
    """Handle Google OAuth callback with proper error handling."""
    # Handle cold-start state expiry
    if not session.get("oauth_state"):
        return redirect(
            "/auth?error=session_expired&message=The+server+restarted+during+sign-in.+Please+try+again."
        )

    try:
        from oauth_utils import google_oauth_callback

        return google_oauth_callback()
    except Exception as e:
        app.logger.error(f"Google OAuth callback error: {e}", exc_info=True)
        if "state" in str(e).lower() or "csrf" in str(e).lower():
            return redirect(
                "/auth?error=session_expired&message=Login+session+expired,+please+try+again"
            )
        return redirect("/auth?error=oauth_failed&message=Sign-in+failed,+please+try+again")


# GitHub OAuth routes
@app.route("/auth/github")
def auth_github():
    """Redirect to GitHub OAuth consent page."""
    from oauth_utils import github_oauth_authorize

    return github_oauth_authorize()


@app.route("/auth/github/callback")
def auth_github_callback():
    """Handle GitHub OAuth callback with proper error handling."""
    # Handle cold-start state expiry
    if not session.get("oauth_state"):
        return redirect(
            "/auth?error=session_expired&message=The+server+restarted+during+sign-in.+Please+try+again."
        )

    try:
        from oauth_utils import github_oauth_callback

        return github_oauth_callback()
    except Exception as e:
        app.logger.error(f"GitHub OAuth callback error: {e}", exc_info=True)
        if "state" in str(e).lower() or "csrf" in str(e).lower():
            return redirect(
                "/auth?error=session_expired&message=Login+session+expired,+please+try+again"
            )
        return redirect("/auth?error=oauth_failed&message=Sign-in+failed,+please+try+again")


@app.route("/signup")
def signup():
    """Redirect to combined auth page (signup side)."""
    return redirect(url_for("auth", tab="signup"))


@app.route("/signup-pro")
def signup_pro():
    """Redirect to combined auth page (signup side)."""
    args = dict(request.args)
    args["tab"] = "signup"
    return redirect(url_for("auth", **args))


@app.route("/api/signup", methods=["POST"])
def signup_submit():
    """Create account: record email (unverified), optional password, send verification link. No card yet—paper trail first."""
    data = request.get_json() or {}
    email = (data.get("email") or "").strip().lower()
    password = (data.get("password") or "").strip()
    if not email or "@" not in email:
        return jsonify({"error": "Valid email required."}), 400
    if password and len(password) < 8:
        return jsonify({"error": "Password must be at least 8 characters."}), 400
    ensure_user_unverified(email, password if password else None)
    token = make_verification_token(email)
    base_url = request.host_url.rstrip("/")
    verify_url = urljoin(base_url + "/", f"verify-email?token={token}")
    send_verification_email(email, verify_url)
    return jsonify(
        {
            "success": True,
            "message": "Check your email for a verification link. Click it to finish setting up your account—then you can choose to go to Pro checkout.",
        }
    )


@app.route("/verify-email")
def verify_email():
    """User clicked the link in their email. Mark verified, create session, send to /verified."""
    token = request.args.get("token", "").strip()
    if not token:
        return redirect(url_for("signup_pro", error="missing_token"))
    email = verify_token(token)
    if not email:
        return redirect(url_for("signup_pro", error="invalid_or_expired"))
    set_user_verified(email)
    sess_token, max_age = session_create(
        email, remember_me=True, user_agent=request.headers.get("User-Agent")
    )
    resp = redirect(url_for("index"))
    if sess_token:
        resp.set_cookie(
            SESSION_COOKIE_NAME,
            sess_token,
            max_age=max_age,
            httponly=True,
            secure=app.config["SESSION_COOKIE_SECURE"],
            samesite=app.config["SESSION_COOKIE_SAMESITE"],
        )
    return resp


@app.route("/verified")
def verified():
    """Shown after email verification. User is logged in (session cookie set); they can go to Pro checkout or back to app."""
    if "user_email" not in session:
        return redirect(url_for("login"))
    return render_template(
        "verified.html",
        email=session["user_email"],
        openclaw_checkout_available=bool(stripe_openclaw_price_id),
        openclaw_enabled=OPENCLAW_ENABLED,
        openclaw_sandbox_root=OPENCLAW_SANDBOX_ROOT,
    )


@app.route("/api/create-checkout", methods=["POST"])
def create_checkout_for_verified():
    """Create Stripe checkout session. Uses session email if logged in and verified; otherwise requires email in body."""
    if not PAYMENTS_ENABLED:
        return api_error("Payments currently unavailable. Please try later.", 503)
    data = request.get_json() or {}
    requested_plan = (data.get("plan") or request.args.get("plan") or "pro").strip().lower()
    plan = "openclaw" if requested_plan in ("openclaw", "claw", "lab") else "pro"
    email = (data.get("email") or "").strip().lower()
    if not email and session.get("user_email") and is_user_verified(session["user_email"]):
        email = session["user_email"]
    if not email or "@" not in email:
        return api_error("Valid email required. Verify your email first, or provide it here.", 400)
    price_id = stripe_price_id
    target_tier = "pro"
    if plan == "openclaw":
        if not stripe_openclaw_price_id:
            return api_error("OpenClaw Lab is not available on this deployment yet.", 400)
        if not OPENCLAW_ENABLED:
            return api_error("OpenClaw Lab is currently disabled by the operator.", 403)
        price_id = stripe_openclaw_price_id
        target_tier = "claw"
    try:
        base_url = request.host_url.rstrip("/")
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[{"price": price_id, "quantity": 1}],
            mode="subscription",
            success_url=f"{base_url}/payment-success?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{base_url}/verified?canceled=1",
            customer_email=email,
            allow_promotion_codes=True,
            metadata={
                "target_tier": target_tier,
                "requested_plan": plan,
                "openclaw_enabled": "1" if OPENCLAW_ENABLED else "0",
            },
        )
        return jsonify(
            {"checkout_url": checkout_session.url, "plan": plan, "target_tier": target_tier}
        )
    except stripe.error.AuthenticationError:
        logger.error("Stripe authentication error - API keys invalid")
        return api_error("Stripe not configured", 503)
    except stripe.error.APIConnectionError:
        logger.error("Stripe API connection error")
        return api_error("Payment service temporarily unavailable", 503)
    except stripe.error.StripeError as e:
        logger.error(f"Stripe error in create-checkout: {str(e)}")
        return api_error("Payment service temporarily unavailable", 503)
    except Exception:
        logger.exception("Create-checkout error")
        return api_error("Something went wrong. Please try again.", 500)


@app.route("/profile")
@login_required
def profile():
    """User profile page with sessions (devices) list."""
    user_email = session["user_email"]
    user_tier = get_user_tier(user_email)
    current_token = request.cookies.get(SESSION_COOKIE_NAME)
    sessions = session_list(user_email, current_token=current_token)
    api_keys = api_key_list(user_email)
    user_row = get_user_row(user_email)
    customer_id = (user_row and user_row["customer_id"]) if user_row else None
    tier_display = tier_label(user_tier)
    specs = get_user_specs(user_email)
    links = get_user_links(user_email)
    return render_template(
        "profile.html",
        email=user_email,
        tier=user_tier,
        tier_display=tier_display,
        sessions=sessions,
        api_keys=api_keys,
        google_oauth_enabled=GOOGLE_OAUTH_ENABLED,
        customer_id=customer_id,
        payments_enabled=PAYMENTS_ENABLED,
        specs=specs,
        links=links,
    )


@app.route("/billing-portal")
@login_required
def billing_portal():
    """Redirect Pro users to Stripe Customer Portal for subscription/billing management. Never buried."""
    if not PAYMENTS_ENABLED:
        return redirect(url_for("profile"))
    user_email = session["user_email"]
    user_tier = get_user_tier(user_email)
    if not has_paid_access(user_tier):
        return redirect(url_for("profile"))
    user_row = get_user_row(user_email)
    customer_id = (user_row and user_row["customer_id"]) if user_row else None
    if not customer_id:
        return redirect(url_for("profile"))
    try:
        portal_session = stripe.billing_portal.Session.create(
            customer=customer_id,
            return_url=request.host_url.rstrip("/") + url_for("profile"),
        )
        return redirect(portal_session.url)
    except stripe.error.AuthenticationError:
        logger.error("Stripe authentication error in billing portal")
        return redirect(url_for("profile", error="stripe_config"))
    except stripe.error.APIConnectionError:
        logger.error("Stripe API connection error in billing portal")
        return redirect(url_for("profile", error="stripe_unavailable"))
    except stripe.error.StripeError as e:
        logger.error(f"Stripe billing portal error: {e}")
        return redirect(url_for("profile", error="stripe_error"))


@app.route("/api/sessions", methods=["GET"])
@login_required_api
def api_sessions_list():
    """List current user's sessions (devices)."""
    user_email = session["user_email"]
    current_token = request.cookies.get(SESSION_COOKIE_NAME)
    return jsonify({"sessions": session_list(user_email, current_token=current_token)})


@app.route("/api/sessions/revoke", methods=["POST"])
@login_required_api
def api_sessions_revoke():
    """Revoke one session by display_id (cannot revoke current session)."""
    user_email = session["user_email"]
    current_token = request.cookies.get(SESSION_COOKIE_NAME)
    data = request.get_json() or {}
    display_id = (data.get("display_id") or "").strip()
    if not display_id:
        return jsonify({"error": "display_id required."}), 400
    sessions = session_list(user_email, current_token=current_token)
    if any(s["display_id"] == display_id and s["current"] for s in sessions):
        return jsonify({"error": "Cannot revoke your current session. Log out instead."}), 400
    if not session_revoke_by_display_id(user_email, display_id):
        return jsonify({"error": "Session not found or already revoked."}), 404
    return jsonify({"success": True})


@app.route("/api/sessions/revoke-others", methods=["POST"])
@login_required_api
def api_sessions_revoke_others():
    """Revoke all sessions except the current one."""
    user_email = session["user_email"]
    current_token = request.cookies.get(SESSION_COOKIE_NAME)
    session_revoke_all_other(user_email, current_token)
    return jsonify({"success": True})


@app.route("/api/developer/keys", methods=["GET"])
@login_required_api
def api_developer_keys_list():
    """List API keys for the current user (prefix and label only; no raw keys)."""
    keys = api_key_list(session["user_email"])
    return jsonify({"keys": keys})


@app.route("/api/developer/keys", methods=["POST"])
@login_required_api
def api_developer_keys_create():
    """Create a new API key. Returns the raw key once — store it securely."""
    data = request.get_json() or {}
    label = (data.get("label") or "").strip()[:64]
    raw, key_id, prefix, label_out, created_at = api_key_create(
        session["user_email"], label=label or None
    )
    if not raw:
        return jsonify({"error": "Failed to create key"}), 500
    return jsonify(
        {
            "key": raw,
            "key_id": key_id,
            "key_prefix": prefix,
            "label": label_out or "",
            "created_at": created_at,
            "message": "Copy this key now. We won’t show it again.",
        }
    )


@app.route("/api/developer/keys/<int:key_id>", methods=["DELETE"])
@login_required_api
def api_developer_keys_revoke(key_id):
    """Revoke an API key by id (must belong to current user)."""
    if not api_key_revoke(session["user_email"], key_id):
        return jsonify({"error": "Key not found or already revoked"}), 404
    return jsonify({"success": True})


@app.route("/api/games", methods=["GET"])
def list_games():
    """Return supported games for the game selector (all Bethesda games with LOOT masterlists)."""
    return jsonify({"games": SUPPORTED_GAMES, "default": DEFAULT_GAME})


# Link preview cache (url -> {title, description, image, cached_at})
_link_preview_cache: dict = {}
_LINK_PREVIEW_CACHE_TTL = 300  # 5 minutes
_LINK_PREVIEW_ALLOWED_DOMAINS = frozenset(
    [
        "nexusmods.com",
        "www.nexusmods.com",
        "tes5edit.github.io",
        "loot.github.io",
        "github.com",
        "www.github.com",
        "youtube.com",
        "www.youtube.com",
        "youtu.be",
        "wabbajack.org",
        "www.wabbajack.org",
        "reddit.com",
        "www.reddit.com",
        "old.reddit.com",
        "silverlock.org",
        "skse.silverlock.org",
        "f4se.silverlock.org",
    ]
)


def _is_preview_domain_allowed(netloc: str) -> bool:
    netloc = (netloc or "").lower()
    netloc_clean = netloc.lstrip("www.") if netloc.startswith("www.") else netloc
    return (
        netloc in _LINK_PREVIEW_ALLOWED_DOMAINS
        or netloc_clean in _LINK_PREVIEW_ALLOWED_DOMAINS
        or any(netloc == d or netloc.endswith("." + d) for d in _LINK_PREVIEW_ALLOWED_DOMAINS)
    )


def _resolve_preview_url(raw_url: str) -> str:
    """Resolve preview URL, allowing same-site relative paths and trusted external URLs."""
    url = (raw_url or "").strip()
    if not url:
        raise ValueError("missing url")
    if url.startswith("/"):
        return request.host_url.rstrip("/") + url
    if not url.startswith(("http://", "https://")):
        raise ValueError("invalid scheme")
    parsed = urlparse(url)
    host = (request.host or "").split(":")[0].lower()
    netloc = (parsed.netloc or "").split(":")[0].lower()
    if netloc == host:
        return url
    if not _is_preview_domain_allowed(netloc):
        raise PermissionError("domain not allowed")
    return url


def _is_internal_preview_url(url: str) -> bool:
    """True when preview URL targets this same deployment host."""
    try:
        from urllib.parse import urlparse

        parsed = urlparse(url)
        netloc = (parsed.netloc or "").split(":")[0].lower()
        host = (request.host or "").split(":")[0].lower()
        return netloc == host
    except Exception:
        return False


def _extract_meta_preview(doc: str, resolved_url: str) -> dict:
    import re

    def _og(s):
        m = re.search(
            r'<meta[^>]+property=["\']og:' + s + r'["\'][^>]+content=["\']([^"\']+)["\']', doc, re.I
        )
        if not m:
            m = re.search(
                r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']og:' + s + r'["\']',
                doc,
                re.I,
            )
        return m.group(1).strip() if m else None

    def _title():
        m = re.search(r"<title[^>]*>([^<]+)</title>", doc, re.I)
        return m.group(1).strip() if m else ""

    title = _og("title") or _title()
    desc = _og("description") or ""
    image = _og("image")
    if image and image.startswith("//"):
        image = "https:" + image
    elif image and image.startswith("/"):
        parsed = urlparse(resolved_url)
        image = f"{parsed.scheme}://{parsed.netloc}{image}"
    return {
        "url": resolved_url,
        "title": title or "",
        "description": (desc or "")[:300],
        "image": image or "",
    }


def _extract_readable_text(doc: str, limit: int = 3000) -> str:
    import re

    text = re.sub(r"(?is)<(script|style)[^>]*>.*?</\1>", " ", doc)
    text = re.sub(r"(?is)<[^>]+>", " ", text)
    text = html.unescape(text)
    text = re.sub(r"\s+", " ", text).strip()
    return text[:limit]


def _fetch_internal_preview_html(resolved_url: str) -> str:
    """Fetch same-site HTML via Flask test client (no external network hop)."""

    parsed = urlparse(resolved_url)
    path = parsed.path or "/"
    if parsed.query:
        path = f"{path}?{parsed.query}"
    # Prevent recursive self-calls through preview endpoints.
    if path.startswith("/api/link-reader") or path.startswith("/api/link-preview"):
        raise ValueError("recursive preview path")

    with app.test_client() as c:
        r = c.get(path)
        if r.status_code >= 400:
            raise ValueError(f"internal preview failed ({r.status_code})")
        return r.get_data(as_text=True) or ""


@app.route("/api/link-preview", methods=["GET"])
@rate_limit(RATE_LIMIT_API, "link-preview")
def api_link_preview():
    """Fetch Open Graph meta for a URL. Obsidian-style hover previews. Whitelisted domains only."""
    raw_url = (request.args.get("url") or "").strip()
    try:
        url = _resolve_preview_url(raw_url)
    except PermissionError:
        return jsonify({"error": "Domain not allowed for preview"}), 403
    except Exception:
        return jsonify({"error": "Invalid URL"}), 400

    if OFFLINE_MODE and not _is_internal_preview_url(url):
        return jsonify(
            {
                "url": url,
                "title": "External preview unavailable in offline mode",
                "description": "Offline mode is enabled. Internal SkyModderAI links still preview normally.",
                "image": "",
                "offline_mode": True,
            }
        )

    now = _time()
    cached = _link_preview_cache.get(url)
    if cached and (now - cached.get("cached_at", 0)) < _LINK_PREVIEW_CACHE_TTL:
        return jsonify({k: v for k, v in cached.items() if k != "cached_at"})

    try:
        r = requests.get(url, timeout=5, headers={"User-Agent": "SkyModderAI/1.0 (link preview)"})
        r.raise_for_status()
        doc = r.text
    except requests.RequestException as e:
        logger.debug("Link preview fetch failed: %s", e)
        return jsonify({"error": "Could not fetch preview"}), 502

    result = _extract_meta_preview(doc, url)
    _link_preview_cache[url] = {**result, "cached_at": now}
    return jsonify(result)


@app.route("/api/link-reader", methods=["GET"])
@rate_limit(RATE_LIMIT_API, "link-preview")
def api_link_reader():
    """Return readable text excerpt for link hover/live preview inside the app."""
    raw_url = (request.args.get("url") or "").strip()
    try:
        url = _resolve_preview_url(raw_url)
    except PermissionError:
        return api_error("Domain not allowed for reader preview", 403)
    except Exception:
        return api_error("Invalid URL", 400)

    if OFFLINE_MODE and not _is_internal_preview_url(url):
        return jsonify(
            {
                "url": url,
                "title": "External reader preview unavailable in offline mode",
                "description": "Offline mode is enabled for this deployment.",
                "content": "External page content is disabled in offline mode. You can still preview internal links and continue using all local analysis features.",
                "offline_mode": True,
            }
        )

    try:
        if _is_internal_preview_url(url):
            doc = _fetch_internal_preview_html(url)
        else:
            r = requests.get(
                url, timeout=6, headers={"User-Agent": "SkyModderAI/1.0 (link reader)"}
            )
            r.raise_for_status()
            doc = r.text
    except requests.RequestException:
        return api_error("Could not fetch page content", 502)
    except Exception:
        return api_error("Could not fetch page content", 502)

    meta = _extract_meta_preview(doc, url)
    content = _extract_readable_text(doc, limit=5000)
    return jsonify(
        {
            "url": url,
            "title": meta.get("title") or "Untitled",
            "description": meta.get("description") or "",
            "content": content,
        }
    )


@app.route("/api/quickstart", methods=["GET"])
def api_quickstart():
    """Return quickstart config: tools, mod managers, learning resources, per-game links, and version info."""
    from quickstart_config import (
        INTERNAL_LINKS,
        LEARNING_RESOURCES,
        MOD_MANAGERS,
        NOOB_JOURNEY,
        TOOLS,
        get_quickstart_for_game,
    )

    game = (request.args.get("game") or DEFAULT_GAME).lower()
    game_data = get_quickstart_for_game(game)
    versions = get_versions_for_game(game)
    if versions:
        game_data["game_versions"] = {
            "default": get_default_version(game),
            "available": list(versions.keys()),
        }
    return jsonify(
        {
            "game": game_data,
            "tools": TOOLS,
            "mod_managers": MOD_MANAGERS,
            "learning_resources": LEARNING_RESOURCES,
            "internal_links": INTERNAL_LINKS,
            "noob_journey": NOOB_JOURNEY,
        }
    )


@app.route("/api/list-preferences/options", methods=["GET"])
def list_preferences_options():
    """Return preference options for the list builder UI."""
    game = (request.args.get("game") or DEFAULT_GAME).lower()
    return jsonify({"options": get_preference_options(game=game), "game": game})


@app.route("/api/list-preferences", methods=["GET", "POST", "PATCH", "DELETE"])
def api_list_preferences():
    """Paid tiers: server-side saved mod lists. Free tier should use localStorage."""
    user_email = session.get("user_email")
    if not user_email:
        return api_error("Login required.", 401)

    if request.method == "GET":
        game = (request.args.get("game") or "").strip().lower() or None
        game_version = (request.args.get("game_version") or "").strip() or None
        masterlist_version = (request.args.get("masterlist_version") or "").strip() or None
        items = list_user_saved_lists(
            user_email, game=game, game_version=game_version, masterlist_version=masterlist_version
        )
        lists = list_user_saved_lists_legacy_map(user_email)
        return jsonify({"success": True, "items": items, "lists": lists})

    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    if request.method == "DELETE":
        list_id = data.get("id")
        if not name and not list_id:
            return api_error("id or name required", 400)
        ok = delete_user_saved_list(
            user_email, name=name, list_id=int(list_id) if list_id else None
        )
        return jsonify({"success": bool(ok)})

    if request.method == "PATCH":
        # Update metadata without changing list_text
        list_id = data.get("id")
        new_name = (data.get("new_name") or "").strip()
        if not list_id and not name:
            return api_error("id or name required", 400)
        try:
            db = get_db()
            updates = []
            params = []
            if new_name:
                updates.append("name = ?")
                params.append(new_name)
            if "game" in data:
                updates.append("game = ?")
                params.append(data["game"].strip().lower())
            if "game_version" in data:
                updates.append("game_version = ?")
                params.append(data["game_version"].strip() or None)
            if "masterlist_version" in data:
                updates.append("masterlist_version = ?")
                params.append(data["masterlist_version"].strip() or None)
            if "tags" in data:
                updates.append("tags = ?")
                params.append(data["tags"].strip() or None)
            if "notes" in data:
                updates.append("notes = ?")
                params.append(data["notes"].strip() or None)
            if "preferences" in data and isinstance(data["preferences"], dict):
                updates.append("preferences_json = ?")
                params.append(json.dumps(data["preferences"]))
            if "source" in data:
                updates.append("source = ?")
                params.append(data["source"].strip() or None)
            if not updates:
                return api_error("No fields to update", 400)
            updates.append("updated_at = CURRENT_TIMESTAMP")
            params.append(user_email.lower())
            if list_id:
                params.append(int(list_id))
                sql = f"UPDATE user_saved_lists SET {', '.join(updates)} WHERE user_email = ? AND id = ?"
            else:
                params.append(name)
                sql = f"UPDATE user_saved_lists SET {', '.join(updates)} WHERE user_email = ? AND name = ?"
            db.execute(sql, params)
            db.commit()
            return jsonify({"success": True})
        except Exception as e:
            logger.warning(f"PATCH list-preferences failed: {e}")
            return api_error("Failed to update list.", 500)

    # Validate and sanitize inputs for POST
    data = request.get_json() or {}
    if not data:
        return api_error("Invalid JSON request body", 400)

    game = validate_game_id(data.get("game", DEFAULT_GAME))
    game_version = (data.get("game_version") or "").strip() or None
    masterlist_version = (data.get("masterlist_version") or "").strip() or None
    tags = (data.get("tags") or "").strip() or None
    notes = (data.get("notes") or "").strip() or None
    preferences = data.get("preferences") if isinstance(data.get("preferences"), dict) else None
    source = (data.get("source") or "").strip() or None
    analysis_snapshot = (
        data.get("analysis_snapshot") if isinstance(data.get("analysis_snapshot"), dict) else None
    )
    list_text = validate_mod_list(data.get("list", ""))
    name = validate_list_name(data.get("name", ""))

    ok = upsert_user_saved_list(
        user_email,
        name,
        game,
        list_text,
        game_version=game_version,
        masterlist_version=masterlist_version,
        tags=tags,
        notes=notes,
        preferences=preferences,
        source=source,
        analysis_snapshot=analysis_snapshot,
    )
    if not ok:
        return api_error("Failed to save list.", 500)
    return api_success(message="List saved successfully")


@app.route("/api/build-list", methods=["POST"])
@rate_limit(RATE_LIMIT_ANALYZE, "build-list")
def api_build_list():
    """Build a mod list from user preferences. All users get standard list; Pro gets AI setups."""
    try:
        data = request.get_json() or {}
        if not data:
            return api_error("Invalid JSON request body", 400)

        # Validate and sanitize inputs
        game = validate_game_id(data.get("game", DEFAULT_GAME))
        preferences = data.get("preferences") if isinstance(data.get("preferences"), dict) else {}

        if not isinstance(preferences, dict):
            preferences = {}

        option_rows = get_preference_options(game=game)
        allowed_pref_values = {
            row["key"]: {c["value"] for c in row.get("choices", [])} for row in option_rows
        }
        sanitized_preferences = {}
        ignored_preferences = []
        for key, value in preferences.items():
            if key not in allowed_pref_values:
                ignored_preferences.append(key)
                continue
            value_s = str(value or "").strip()
            if value_s in allowed_pref_values[key]:
                sanitized_preferences[key] = value_s
            else:
                sanitized_preferences[key] = "any"

        limit = validate_limit(data.get("limit"), default=50, max_allowed=100)
        specs = data.get("specs") or {}
        if isinstance(specs, dict):
            specs = {k: v for k, v in specs.items() if v}
        user_email = session.get("user_email")
        if not specs and user_email:
            specs = get_user_specs(user_email) or {}
        if isinstance(specs, dict):
            specs = {k: v for k, v in specs.items() if v}
        is_pro = True  # All users get full features

        try:
            p = get_parser(game)
            nexus_slug = NEXUS_GAME_SLUGS.get(game, "skyrimspecialedition")
            mods = build_list_from_preferences(
                p, game, nexus_slug, sanitized_preferences, limit=limit, specs=specs
            )
        except Exception:
            logger.exception("Build list error")
            return api_error("Failed to build list. Try again.", 500)

        result = {
            "mods": mods,
            "game": game,
            "preferences": sanitized_preferences,
            "ignored_preferences": ignored_preferences,
        }

        # Pro: AI-generated multiple setups (future: call OpenAI for N combinations)
        if is_pro and AI_CHAT_ENABLED and data.get("pro_setups"):
            try:
                setups = _ai_generate_setups(
                    game, sanitized_preferences, nexus_slug, p, limit=3, specs=specs
                )
                result["setups"] = setups
            except Exception as e:
                logger.debug("AI setups failed: %s", e)

        track_activity(
            "build_list",
            {
                "game": game,
                "mods_returned": len(result.get("mods") or []),
                "has_setups": bool(result.get("setups")),
            },
            user_email,
        )
        return api_success(result)

    except Exception as e:
        logger.exception("Build list endpoint failed: %s", e)
        return api_error("Failed to build list. Please try again.", 500)


def _ai_generate_setups(game, preferences, nexus_slug, parser, limit=3, specs=None):
    """Pro: Generate multiple mod list setups via AI. Returns list of {name, mods, rationale}."""
    if not LLM_API_KEY:
        return []
    specs = specs or {}
    prefs_str = ", ".join(f"{k}={v}" for k, v in preferences.items() if v and v != "any")
    spec_str = ""
    if specs and any(specs.values()):
        spec_parts = [f"{k}: {v}" for k, v in specs.items() if v]
        spec_str = f" User's system: {', '.join(spec_parts)}. Tailor setups to their rig (e.g. favor performance mods for low VRAM)."
    prompt = f"""Generate {limit} distinct mod list setups for {game} with preferences: {prefs_str or "general"}.{spec_str} Each setup should have a short name, 8-15 mod names (exact plugin names from LOOT), and a one-line rationale. Return JSON array: [{{"name":"...","mods":["Mod1.esp",...],"rationale":"..."}}]. Use only real mod names from the LOOT masterlist."""
    try:
        client = get_ai_client()
        r = client.chat.completions.create(
            model=LLM_MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=800,
            temperature=0.7,
        )
        text = (r.choices[0].message.content or "").strip()
        import json
        import re

        json_match = re.search(r"\[[\s\S]*\]", text)
        if json_match:
            setups = json.loads(json_match.group())
            nexus_base = f"https://www.nexusmods.com/games/{nexus_slug}/mods?keyword="
            from urllib.parse import quote

            for s in setups[:limit]:
                mods = s.get("mods") or []
                s["mods"] = [{"name": m, "nexus_url": nexus_base + quote(m)} for m in mods if m]
            return setups[:limit]
    except Exception as e:
        logger.debug("AI setups parse error: %s", e)
    return []


@app.route("/api/analyze/summary", methods=["POST"])
@rate_limit(RATE_LIMIT_ANALYZE, "ai_summary")
def api_analyze_summary():
    """Generate a high-level strategic summary of the analysis using AI."""
    if not AI_CHAT_ENABLED:
        return jsonify({"error": "AI not enabled"}), 503

    data = request.get_json() or {}
    context = data.get("context") or ""

    if not context:
        return jsonify({"summary": ""})

    system = (
        "You are SkyModderAI, an expert modding engineer. Analyze the provided load order report and provide a 'Strategic Plan'. "
        "1. Executive Summary: State of the build (Stable/Critical/Messy). "
        "2. Top Priorities: The 3 most important things to fix immediately. "
        "3. Plan of Attack: A brief, encouraging, professional path forward. "
        "Be concise, authoritative, and well-spoken."
    )

    try:
        client = get_ai_client()
        r = client.chat.completions.create(
            model=LLM_MODEL,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": context[:15000]}
            ],
            max_tokens=600,
            temperature=0.3,
        )
        summary = (r.choices[0].message.content or "").strip()
        return jsonify({"summary": summary})
    except Exception as e:
        logger.error(f"AI Summary error: {e}")
        return jsonify({"error": "Could not generate summary."}), 500


@app.route("/api/compose-guide", methods=["POST"])
@rate_limit(RATE_LIMIT_ANALYZE, "compose_guide")
def api_compose_guide():
    """Compose a professional PDF-ready guide from the current fix steps."""
    if not AI_CHAT_ENABLED:
        return jsonify({"error": "AI not enabled"}), 503

    data = request.get_json() or {}
    steps = data.get("steps") or []
    game = data.get("game") or "Unknown Game"

    if not steps:
        return jsonify({"document": ""})

    # Format steps for AI context
    steps_text = "\n".join([f"{i+1}. [{s.get('type', 'step').upper()}] {s.get('content') or s.get('message') or ''}" for i, s in enumerate(steps)])

    system = (
        "You are SkyModderAI. The user has a list of modding issues and steps. "
        "Compose a beautiful, well-spoken, professional guide based on these steps. "
        "Use Markdown. "
        "Structure it as: 'Executive Summary', 'Action Plan' (step-by-step), and 'Final Verification'. "
        "The tone should be expert, reassuring, and clear. This text will be converted to a PDF."
    )

    try:
        client = get_ai_client()
        r = client.chat.completions.create(
            model=LLM_MODEL,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": f"Game: {game}\n\nRaw Steps:\n{steps_text}"}
            ],
            max_tokens=2500,
            temperature=0.3,
        )
        document = (r.choices[0].message.content or "").strip()
        return jsonify({"document": document})
    except Exception as e:
        logger.error(f"AI Compose error: {e}")
        return jsonify({"error": "Could not compose guide."}), 500


# Community: blocklist for moderation (hate, harassment, spam patterns)
# Minimal blocklist: hate, harassment, illegal. Utilitarian—we draw the line at harm, not opinion.
_COMMUNITY_BLOCKLIST = frozenset(
    [
        "kill yourself",
        "kys",
        "die ",
        " go die",
        "unalive",
        "harass",
        "dox ",
        "nazi",
        "hitler",
        "rape",
        "pedo",
        "pedophile",
        "slur",
        "retard",
        "faggot",
        "nigger",
        "nigga",
        "chink",
        "spic",
        "kike",
        "gook",
        "tranny",
        "human trafficking",
        "drug trafficking",
        "buy cocaine",
        "sell meth",
        "hitman for hire",
        "hire a hitman",
    ]
)


def _community_content_ok(content: str) -> bool:
    """Check if post content passes basic moderation."""
    if not content or len(content.strip()) < 3:
        return False
    if len(content) > 2000:
        return False
    lower = content.lower()
    return not any(blocked in lower for blocked in _COMMUNITY_BLOCKLIST)


COMMUNITY_TAGS = [
    "general",
    "tip",
    "help",
    "celebration",
    "skyrim",
    "fallout",
    "starfield",
    "tool",
    "dev",
    "character",
    "structure",
    "spell",
    "modlist",
]


@app.route("/api/community/posts", methods=["GET"])
def api_community_posts_list():
    """List community posts with replies, votes, Pro badge. Public. sort=new|top|hot."""
    try:
        limit = min(max(1, int(request.args.get("limit", 50))), 100)
        offset = max(0, int(request.args.get("offset", 0)))
        tag = (request.args.get("tag") or "").strip().lower()
        q = (request.args.get("q") or "").strip()
        sort = (request.args.get("sort") or "new").strip().lower()
        if sort not in ("new", "top", "hot"):
            sort = "new"
        db = get_db()
        sql = """SELECT p.id, p.user_email, p.content, p.tag, p.created_at,
                 COALESCE((SELECT SUM(v.vote) FROM community_votes v WHERE v.post_id = p.id AND v.vote > 0), 0) AS vote_sum,
                 (SELECT COUNT(*) FROM community_replies r WHERE r.post_id = p.id AND r.moderated = 0) AS reply_count
                 FROM community_posts p WHERE p.moderated = 0"""
        params = []
        if tag and tag in COMMUNITY_TAGS:
            sql += " AND p.tag = ?"
            params.append(tag)
        if q:
            sql += " AND (p.content LIKE ? OR p.tag LIKE ?)"
            params.extend([f"%{q}%", f"%{q}%"])
        if sort == "top":
            sql += " ORDER BY vote_sum DESC, p.created_at DESC"
        elif sort == "hot":
            sql += """ ORDER BY (vote_sum + 1) / (1.0 + julianday('now') - julianday(p.created_at)) DESC, p.created_at DESC"""
        else:
            sql += " ORDER BY p.created_at DESC"
        sql += " LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        rows = db.execute(sql, params).fetchall()
        posts = []
        for r in rows:
            tier = get_user_tier(r["user_email"])
            reply_rows = db.execute(
                "SELECT id, user_email, content, created_at FROM community_replies WHERE post_id = ? AND moderated = 0 ORDER BY created_at ASC",
                (r["id"],),
            ).fetchall()
            vote_sum = (
                db.execute(
                    "SELECT COALESCE(SUM(vote), 0) FROM community_votes WHERE post_id = ?",
                    (r["id"],),
                ).fetchone()[0]
                or 0
            )
            my_vote = 0
            if session.get("user_email"):
                v = db.execute(
                    "SELECT vote FROM community_votes WHERE post_id = ? AND user_email = ?",
                    (r["id"], session["user_email"].lower()),
                ).fetchone()
                if v:
                    my_vote = v["vote"]
            posts.append(
                {
                    "id": r["id"],
                    "user": _redact_email(r["user_email"]),
                    "content": r["content"],
                    "tag": r["tag"] or "general",
                    "created_at": r["created_at"],
                    "is_pro": has_paid_access(tier),
                    "replies": [
                        {
                            "id": rr["id"],
                            "user": _redact_email(rr["user_email"]),
                            "content": rr["content"],
                            "created_at": rr["created_at"],
                            "is_pro": has_paid_access(get_user_tier(rr["user_email"])),
                        }
                        for rr in reply_rows
                    ],
                    "votes": vote_sum,
                    "my_vote": my_vote,
                }
            )
        return jsonify({"posts": posts, "tags": COMMUNITY_TAGS})
    except Exception as e:
        logger.exception("Community posts list error: %s", e)
        return jsonify({"posts": [], "tags": COMMUNITY_TAGS})


@app.route("/api/community/posts", methods=["POST"])
@login_required_api
@rate_limit(RATE_LIMIT_API, "community")
def api_community_posts_create():
    """Create a community post. Requires login. Content filtered for hate/harassment."""
    data = request.get_json() or {}
    content = (data.get("content") or "").strip()
    tag = (data.get("tag") or "general").strip().lower()
    if tag not in COMMUNITY_TAGS:
        tag = "general"
    if not _community_content_ok(content):
        return jsonify(
            {
                "error": "Post must be 3–2000 characters and follow community guidelines. See the guidelines in the Community tab."
            }
        ), 400
    try:
        db = get_db()
        db.execute(
            "INSERT INTO community_posts (user_email, content, tag, moderated) VALUES (?, ?, ?, 0)",
            (session["user_email"].lower(), content, tag),
        )
        db.commit()
        row = db.execute(
            "SELECT id, created_at FROM community_posts WHERE id = last_insert_rowid()"
        ).fetchone()
        track_activity(
            "community_post_create", {"post_id": row["id"], "tag": tag}, session.get("user_email")
        )
        return jsonify({"success": True, "id": row["id"], "created_at": row["created_at"]})
    except Exception as e:
        logger.exception("Community post create error: %s", e)
        return jsonify({"error": "Failed to post"}), 500


@app.route("/api/community/posts/<int:post_id>/replies", methods=["POST"])
@login_required_api
@rate_limit(RATE_LIMIT_API, "community")
def api_community_reply(post_id):
    """Add a reply to a post."""
    data = request.get_json() or {}
    content = (data.get("content") or "").strip()
    if not _community_content_ok(content):
        return jsonify(
            {"error": "Reply must be 3–2000 characters and follow community guidelines."}
        ), 400
    try:
        db = get_db()
        exists = db.execute(
            "SELECT 1 FROM community_posts WHERE id = ? AND moderated = 0", (post_id,)
        ).fetchone()
        if not exists:
            return jsonify({"error": "Post not found"}), 404
        db.execute(
            "INSERT INTO community_replies (post_id, user_email, content, moderated) VALUES (?, ?, ?, 0)",
            (post_id, session["user_email"].lower(), content),
        )
        db.commit()
        row = db.execute(
            "SELECT id, created_at FROM community_replies WHERE id = last_insert_rowid()"
        ).fetchone()
        track_activity(
            "community_reply_create",
            {"post_id": post_id, "reply_id": row["id"]},
            session.get("user_email"),
        )
        return jsonify({"success": True, "id": row["id"], "created_at": row["created_at"]})
    except Exception as e:
        logger.exception("Community reply error: %s", e)
        return jsonify({"error": "Failed to reply"}), 500


@app.route("/api/community/posts/<int:post_id>/vote", methods=["POST"])
@login_required_api
def api_community_vote(post_id):
    """Vote on a post (1 or 0 to remove)."""
    data = request.get_json() or {}
    vote = data.get("vote", 0)
    if vote not in (1, 0):
        return jsonify({"error": "Invalid vote (upvotes only)"}), 400
    try:
        db = get_db()
        exists = db.execute(
            "SELECT 1 FROM community_posts WHERE id = ? AND moderated = 0", (post_id,)
        ).fetchone()
        if not exists:
            return jsonify({"error": "Post not found"}), 404
        email = session["user_email"].lower()
        db.execute(
            "DELETE FROM community_votes WHERE post_id = ? AND user_email = ?", (post_id, email)
        )
        if vote != 0:
            db.execute(
                "INSERT INTO community_votes (post_id, user_email, vote) VALUES (?, ?, ?)",
                (post_id, email, vote),
            )
        db.commit()
        total = (
            db.execute(
                "SELECT COALESCE(SUM(vote), 0) FROM community_votes WHERE post_id = ?", (post_id,)
            ).fetchone()[0]
            or 0
        )
        track_activity(
            "community_vote",
            {"post_id": post_id, "vote": vote, "votes_total": total},
            session.get("user_email"),
        )
        return jsonify({"success": True, "votes": total})
    except Exception as e:
        logger.exception("Community vote error: %s", e)
        return jsonify({"error": "Failed to vote"}), 500


@app.route("/api/refresh-masterlist", methods=["POST"])
@rate_limit(RATE_LIMIT_ANALYZE, "refresh")
def refresh_masterlist():
    """Force re-download and re-parse the masterlist for a game so search and analyze use the latest LOOT data."""
    data = request.get_json() or {}
    game = (data.get("game") or request.args.get("game") or DEFAULT_GAME).lower()
    if game not in {g["id"] for g in SUPPORTED_GAMES}:
        return jsonify({"error": "Unknown game"}), 400
    version_key = "latest"
    key = (game, version_key)
    try:
        p = LOOTParser(game, version="latest")
        if p.download_masterlist(force_refresh=True):
            p.parse_masterlist()
            p.save_database()
            if key in _parsers:
                _parsers[key] = p
            return jsonify({"success": True, "game": game, "mod_count": len(p.mod_database)})
    except Exception as e:
        logger.exception("Refresh masterlist failed: %s", e)
        return jsonify({"error": "Refresh failed"}), 500
    return jsonify({"error": "Could not download masterlist"}), 502


@app.route("/api/sample-mod-list", methods=["GET"])
def get_sample_mod_list():
    """Return a game-specific sample mod list (typical base + DLC + common first downloads, some may conflict)."""
    game = (request.args.get("game") or "").strip().lower()
    if not game or game not in SAMPLE_MOD_LISTS:
        game = DEFAULT_GAME
    mod_list = SAMPLE_MOD_LISTS.get(game, SAMPLE_MOD_LISTS[DEFAULT_GAME])
    return jsonify({"game": game, "mod_list": mod_list})


@app.route("/api/games/<game_id>/masterlist-versions", methods=["GET"])
def list_masterlist_versions(game_id):
    """Return available masterlist versions for a game (for version picking: older systems, abandoned mods)."""
    game_id = (game_id or "").lower()
    if game_id not in {g["id"] for g in SUPPORTED_GAMES}:
        return jsonify({"versions": [], "error": "Unknown game"}), 404
    versions = LOOTParser.fetch_masterlist_versions(game_id)
    return jsonify(
        {
            "game": game_id,
            "versions": versions,
            "latest": LOOTParser.LATEST_VERSIONS.get(game_id, "0.26"),
        }
    )


@app.route("/api/games/<game_id>/game-versions", methods=["GET"])
def list_game_versions(game_id):
    """Return available game executable versions for version-aware analysis."""
    game_id = (game_id or "").lower()
    if game_id not in {g["id"] for g in SUPPORTED_GAMES}:
        return jsonify({"versions": {}, "default": "", "error": "Unknown game"}), 404
    versions = get_versions_for_game(game_id)
    default = get_default_version(game_id)
    return jsonify({"game": game_id, "versions": versions, "default": default})


@app.route("/api/mod-search", methods=["GET"])
@rate_limit(RATE_LIMIT_SEARCH, "search")
def mod_search():
    """Search mod names for typeahead/lookup. ?q=sky&game=skyrimse&version=0.26&limit=10
    Uses BM25 ranking + query expansion (USSEP, SKSE, etc.). Pro users get web search fallback."""
    q = (request.args.get("q") or "").strip()
    game = (request.args.get("game") or DEFAULT_GAME).lower()
    version = (request.args.get("version") or "").strip() or "latest"
    allowed = {g["id"] for g in SUPPORTED_GAMES}
    if game not in allowed:
        game = DEFAULT_GAME
    try:
        limit = min(max(1, int(request.args.get("limit", 25))), 40)
    except (TypeError, ValueError):
        limit = 25
    if not q:
        return jsonify({"matches": [], "web_suggestions": []})
    user_email = session.get("user_email")
    is_pro = True
    try:
        p = get_parser(game, version=version)
        engine = get_search_engine(p)
        results = engine.search(q, limit=limit)
        matches = [r.mod_name for r in results]
        payload = {"matches": matches}
        # Pro-only: web search fallback when DB has few or no results
        if is_pro and len(matches) < 8:
            try:
                from web_search import search_mods_web

                game_obj = next((g for g in SUPPORTED_GAMES if g["id"] == game), None)
                game_name = game_obj["name"] if game_obj else "Skyrim"
                nexus_slug = game_obj["nexus_slug"] if game_obj else "skyrimspecialedition"
                web_results = search_mods_web(
                    query=q,
                    game_display_name=game_name,
                    nexus_slug=nexus_slug,
                    max_results=12,
                )
                payload["web_suggestions"] = web_results
            except Exception as e:
                logger.warning("Web search fallback failed: %s", e)
                payload["web_suggestions"] = []
        else:
            payload["web_suggestions"] = []
        return jsonify(payload)
    except Exception as e:
        logger.exception("Mod search failed: %s", e)
        return jsonify({"matches": [], "web_suggestions": []})


@app.route("/api/modlist/normalize", methods=["POST"])
@rate_limit(RATE_LIMIT_SEARCH, "search")
def normalize_modlist_input():
    """
    Parse/normalize user mod list input and return best-effort LOOT matches.
    Supports messy input (paths, MO2/plugins.txt markers, typos) and returns:
    - normalized_text (plugins-style markers)
    - per-entry matching metadata with top suggestions
    """
    data = request.get_json() or {}
    mod_list_text = data.get("mod_list") or ""
    game = (data.get("game") or DEFAULT_GAME).lower()
    if game not in {g["id"] for g in SUPPORTED_GAMES}:
        game = DEFAULT_GAME
    if not isinstance(mod_list_text, str) or not mod_list_text.strip():
        return api_error("mod_list required", 400)
    if len(mod_list_text) > MAX_INPUT_SIZE:
        return api_error(f"mod_list too large (max {MAX_INPUT_SIZE} chars)", 413)

    try:
        entries = parse_mod_list_text(mod_list_text)
        p = get_parser(game)
        engine = get_search_engine(p)
        nexus_slug = NEXUS_GAME_SLUGS.get(game, "skyrimspecialedition")
        nexus_base = f"https://www.nexusmods.com/games/{nexus_slug}/mods"

        normalized_lines = []
        out_entries = []

        for idx, entry in enumerate(entries[:600]):
            original_name = (entry.name or "").strip()
            if not original_name:
                continue

            best_name = original_name
            match_type = "unknown"
            confidence = 0.0
            suggestions = []

            mod_info = p.get_mod_info(original_name)
            if mod_info:
                best_name = mod_info.name
                match_type = "exact"
                confidence = 1.0
                suggestions = [mod_info.name]
            else:
                fuzzy = p.get_fuzzy_suggestion(original_name, cutoff=0.72)
                if fuzzy:
                    best_name = fuzzy
                    match_type = "fuzzy"
                    confidence = 0.84
                    suggestions = [fuzzy]
                search_hits = engine.search(original_name, limit=4)
                search_suggestions = [h.mod_name for h in search_hits]
                if match_type == "unknown" and search_suggestions:
                    top_score = float(getattr(search_hits[0], "score", 0.0) or 0.0)
                    # Only treat search as a confident match when score clears a floor.
                    if top_score >= 1.8:
                        best_name = search_suggestions[0]
                        match_type = "search"
                        confidence = max(0.68, min(0.92, round(top_score / 8.0, 2)))
                # Keep unique order, fuzzy first if present.
                merged = []
                for n in suggestions + search_suggestions:
                    if n and n not in merged:
                        merged.append(n)
                suggestions = merged[:4]

            prefix = "*" if entry.enabled else "-"
            line_name = best_name if match_type in ("exact", "fuzzy", "search") else original_name
            normalized_lines.append(f"{prefix}{line_name}")
            keyword = best_name or original_name
            out_entries.append(
                {
                    "index": idx,
                    "original": original_name,
                    "enabled": bool(entry.enabled),
                    "normalized": best_name,
                    "match_type": match_type,
                    "confidence": confidence,
                    "suggestions": suggestions,
                    "nexus_url": f"{nexus_base}?{urlencode({'keyword': keyword})}",
                }
            )

        return jsonify(
            {
                "game": game,
                "entries": out_entries,
                "normalized_text": "\n".join(normalized_lines),
                "summary": {
                    "total": len(out_entries),
                    "exact": sum(1 for e in out_entries if e["match_type"] == "exact"),
                    "fuzzy": sum(1 for e in out_entries if e["match_type"] == "fuzzy"),
                    "search": sum(1 for e in out_entries if e["match_type"] == "search"),
                    "unknown": sum(1 for e in out_entries if e["match_type"] == "unknown"),
                },
            }
        )
    except Exception:
        logger.exception("Modlist normalize failed")
        return api_error("Could not normalize mod list", 500)


@app.route("/api/recommendations", methods=["GET", "POST"])
def api_recommendations():
    """Get mod recommendations based on current list. Updates live as user adds mods.
    GET: ?game=skyrimse&mods=Mod1.esp,Mod2.esp&limit=8&for_ai=1
    POST: body {game, mod_list: [...], limit, for_ai}
    When for_ai=1: returns top_picks {utility, design, fun, environmental} for Pro AI."""
    if request.method == "GET":
        game = (request.args.get("game") or DEFAULT_GAME).lower()
        mods_param = request.args.get("mods") or request.args.get("mod_list") or ""
        mod_list = [m.strip() for m in mods_param.split(",") if m.strip()]
        try:
            limit = min(max(1, int(request.args.get("limit", 8))), 20)
        except (TypeError, ValueError):
            limit = 8
    else:
        data = request.get_json() or {}
        game = (data.get("game") or DEFAULT_GAME).lower()
        mod_list = data.get("mod_list") or data.get("mods") or []
        if isinstance(mod_list, str):
            mod_list = [m.strip() for m in mod_list.split(",") if m.strip()]
        try:
            limit = min(max(1, int(data.get("limit", 8))), 20)
        except (TypeError, ValueError):
            limit = 8
    if game not in {g["id"] for g in SUPPORTED_GAMES}:
        game = DEFAULT_GAME
    nexus_slug = NEXUS_GAME_SLUGS.get(game, "skyrimspecialedition")
    for_ai = request.args.get("for_ai") or (request.get_json() or {}).get("for_ai")
    for_ai = str(for_ai).lower() in ("1", "true", "yes")
    mod_list_text = (request.get_json() or {}).get("mod_list_text", "")
    specs = (request.get_json() or {}).get("specs") or {}
    try:
        p = get_parser(game)
        if for_ai:
            payload = get_recommendations_for_ai(
                p, mod_list, game, nexus_slug, limit=limit, top_picks_per_category=2
            )
            out = {
                "recommendations": payload["recommendations"],
                "top_picks": payload["top_picks"],
                "game": game,
            }
        else:
            recs = get_recommendations(
                p, mod_list, game, nexus_slug, limit=limit, include_category=True
            )
            out = {"recommendations": recs, "game": game}
        # Dynamic warnings (plugin limit, system strain)
        out["warnings"] = get_mod_warnings(
            mod_list_text=mod_list_text or None,
            mod_list=mod_list,
            game=game,
            specs=specs,
        )
        return jsonify(out)
    except Exception as e:
        logger.exception("Recommendations failed: %s", e)
        return jsonify({"recommendations": [], "warnings": [], "game": game})


@app.route("/api/search", methods=["GET"])
def full_search():
    """Full-featured search for AI assistant and power users. ?q=ordinator&game=skyrimse&limit=15&for_ai=1
    Returns BM25-ranked results with scores, snippets, mod_info (requirements, tags)."""
    try:
        # Validate and sanitize inputs
        q = validate_search_query(request.args.get("q", ""))
        game = validate_game_id(request.args.get("game", DEFAULT_GAME))
        version = (request.args.get("version") or "").strip() or "latest"
        limit = validate_limit(request.args.get("limit"), default=15, max_allowed=50)
        for_ai = request.args.get("for_ai", "0").lower() in ("1", "true", "yes")

        p = get_parser(game, version=version)
        engine = get_search_engine(p)

        if for_ai:
            results = engine.search_for_ai(q, limit=limit)
            return api_success({"results": results, "game": game})

        results = engine.search(q, limit=limit, include_breakdown=True)
        out = []
        for r in results:
            # Build related links for each search result
            links = {}

            # Nexus link if available
            if r.mod_info and r.mod_info.get("nexus_id"):
                nexus_game = next(
                    (g["nexus_slug"] for g in SUPPORTED_GAMES if g["id"] == game), None
                )
                if nexus_game:
                    links["nexus"] = (
                        f"https://nexusmods.com/{nexus_game}/mods/{r.mod_info['nexus_id']}"
                    )

            # Analysis link
            links["analyze"] = f"/api/analyze?game={game}&mods={quote(r.mod_name)}"

            # Search for conflicts/solutions
            links["conflicts"] = (
                f"/api/search-solutions?q={quote(r.mod_name + ' conflict')}&game={game}"
            )
            links["solutions"] = f"/api/search-solutions?q={quote(r.mod_name + ' fix')}&game={game}"

            # Add to current list (via client-side)
            links["add_to_list"] = f"client:addMod:{r.mod_name}"

            out.append(
                {
                    "mod_name": r.mod_name,
                    "score": r.score,
                    "score_breakdown": r.score_breakdown,
                    "snippet": r.snippet,
                    "mod_info": r.mod_info,
                    "links": links,
                }
            )
        return jsonify({"results": out, "game": game, "query": q})
    except Exception as e:
        logger.exception("Full search failed: %s", e)
        return jsonify({"results": [], "game": game or DEFAULT_GAME})


@app.route("/api/info", methods=["GET"])
def api_info():
    """Machine-readable feature discovery for assistants and developers.
    Returns available endpoints, their methods, expected inputs/outputs, and feature flags."""
    return jsonify(
        {
            "name": "SkyModderAI API",
            "version": "1.0",
            "description": "Bethesda mod compatibility analysis, ranking, build generation, and dev tooling using LOOT data.",
            "endpoints": {
                "/api/analyze": {
                    "methods": ["POST"],
                    "description": "Analyze a mod list for conflicts, warnings, and suggested load order",
                    "input": {
                        "mod_list": "string (required) - Newline-separated mod list",
                        "game": "string (optional) - Game ID (skyrimse, skyrim, fallout4, etc.)",
                        "game_version": "string (optional) - Game executable version",
                        "masterlist_version": "string (optional) - LOOT masterlist version",
                        "specs": "object (optional) - User system specs",
                    },
                    "output": {
                        "conflicts": "object - Errors, warnings, info with links",
                        "suggested_load_order": "array - Ordered list of mods",
                        "summary": "object - Conflict counts",
                        "_links": "object - Related resource URLs",
                    },
                    "rate_limit": "10 requests per minute",
                    "tier_access": "all",
                },
                "/api/search": {
                    "methods": ["GET"],
                    "description": "Search for mods by name with BM25 ranking",
                    "input": {
                        "q": "string (required) - Search query",
                        "game": "string (optional) - Game ID",
                        "limit": "integer (optional) - Max results (1-50, default 15)",
                        "for_ai": "boolean (optional) - AI-optimized format",
                    },
                    "output": {
                        "results": "array - Mod objects with scores and links",
                        "query": "string - The search query used",
                    },
                    "rate_limit": "30 requests per minute",
                    "tier_access": "all",
                },
                "/api/build-list": {
                    "methods": ["POST"],
                    "description": "Build a mod list from user preferences",
                    "input": {
                        "game": "string (optional) - Game ID",
                        "preferences": "object - User preference options",
                    },
                    "output": {
                        "mods": "array - Generated mod list",
                        "setups": "array - AI-generated setups (Pro+ only)",
                    },
                    "rate_limit": "5 requests per minute",
                    "tier_access": "all (AI setups for Pro+)",
                },
                "/api/list-preferences": {
                    "methods": ["GET", "POST", "PATCH", "DELETE"],
                    "description": "Manage saved mod lists with metadata (Pro feature)",
                    "input": {
                        "GET": "game, game_version, masterlist_version as query params",
                        "POST": "name, game, list, game_version, masterlist_version, tags, notes, preferences, source",
                        "PATCH": "id or name + fields to update",
                        "DELETE": "id or name",
                    },
                    "output": {
                        "items": "array - Saved list objects with metadata",
                        "lists": "object - Legacy format map",
                    },
                    "rate_limit": "20 requests per minute",
                    "tier_access": "Pro, OpenClaw",
                },
                "/api/community/posts": {
                    "methods": ["GET", "POST"],
                    "description": "Community posts and discussions",
                    "input": {"GET": "sort, tag, search as query params", "POST": "tag, content"},
                    "output": {
                        "posts": "array - Community post objects",
                        "health": "object - Community metrics",
                    },
                    "rate_limit": "10 posts per minute",
                    "tier_access": "all (posting requires login)",
                },
                "/api/games": {
                    "methods": ["GET"],
                    "description": "Get supported games and metadata",
                    "output": {"games": "array - Game objects with IDs, names, nexus_slugs"},
                    "tier_access": "all",
                },
                "/api/user/me": {
                    "methods": ["GET"],
                    "description": "Get current user profile and tier",
                    "output": {
                        "email": "string",
                        "tier": "string - free, pro, claw",
                        "specs": "object - User system specs",
                    },
                    "tier_access": "login required",
                },
            },
            "features": {
                "conflict_detection": True,
                "load_order_optimization": True,
                "mod_search": True,
                "saved_lists": True,
                "ai_chat": True,
                "build_lists": True,
                "community": True,
                "dev_tools": True,
                "cross_tab_sync": True,
                "context_aware_navigation": True,
                "hal_links": True,
            },
            "games": [
                {
                    "id": "skyrimse",
                    "name": "Skyrim Special Edition",
                    "nexus_slug": "skyrimspecialedition",
                },
                {"id": "skyrim", "name": "Skyrim LE", "nexus_slug": "skyrim"},
                {"id": "skyrimvr", "name": "Skyrim VR", "nexus_slug": "skyrimvr"},
                {"id": "oblivion", "name": "Oblivion", "nexus_slug": "oblivion"},
                {"id": "fallout3", "name": "Fallout 3", "nexus_slug": "fallout3"},
                {"id": "falloutnv", "name": "Fallout New Vegas", "nexus_slug": "newvegas"},
                {"id": "fallout4", "name": "Fallout 4", "nexus_slug": "fallout4"},
                {"id": "starfield", "name": "Starfield", "nexus_slug": "starfield"},
            ],
            "tiers": {
                "free": {"limits": "Basic analysis, search, community"},
                "pro": {"limits": "Saved lists, AI setups, advanced features"},
                "claw": {"limits": "All features + OpenClaw automation"},
            },
            "_links": {
                "self": {"href": "/api/info", "title": "API Information"},
                "analyze": {"href": "/api/analyze", "title": "Analyze mod list"},
                "search": {"href": "/api/search", "title": "Search mods"},
                "docs": {"href": "/api", "title": "API Documentation"},
                "community": {"href": "/api/community/posts", "title": "Community"},
            },
        }
    )


@app.route("/api/ai-context", methods=["GET", "POST"])
def ai_context():
    """Build structured context for AI assistant. GET: ?game=skyrimse&query=ctd
    POST: body with game, conflicts[], mod_list[], specs{}, user_query.
    Returns knowledge index (resolutions, esoteric solutions, game resources)."""
    if request.method == "GET":
        game = (request.args.get("game") or DEFAULT_GAME).lower()
        user_query = (request.args.get("query") or "").strip()
        ctx = build_knowledge_context(
            game_id=game, conflicts=[], mod_list=[], specs=None, user_query=user_query
        )
        return jsonify(ctx)
    data = request.get_json() or {}
    game = (data.get("game") or DEFAULT_GAME).lower()
    conflicts = data.get("conflicts") or []
    mod_list = data.get("mod_list") or []
    specs = data.get("specs") or {}
    user_query = (data.get("user_query") or data.get("query") or "").strip()
    ctx = build_knowledge_context(
        game_id=game,
        conflicts=conflicts,
        mod_list=mod_list,
        specs=specs,
        user_query=user_query,
    )
    return jsonify(ctx)


@app.route("/api/search-solutions", methods=["GET"])
def search_solutions():
    """Search web for scattered solutions (Reddit, Nexus). ?q=ctd+skyrim&game=skyrimse&limit=8
    Pro-only: finds esoteric fixes from community posts."""
    q = (request.args.get("q") or request.args.get("query") or "").strip()
    game = (request.args.get("game") or DEFAULT_GAME).lower()
    try:
        limit = min(max(1, int(request.args.get("limit", 8))), 20)
    except (TypeError, ValueError):
        limit = 8
    if not q:
        return jsonify({"solutions": [], "error": "q or query required"})
    try:
        from web_search import search_solutions_web

        game_obj = next((g for g in SUPPORTED_GAMES if g["id"] == game), None)
        game_name = game_obj["name"] if game_obj else "Skyrim"
        results = search_solutions_web(query=q, game_display_name=game_name, max_results=limit)
        return jsonify({"solutions": results, "game": game})
    except Exception as e:
        logger.warning("Search solutions failed: %s", e)
        return jsonify({"solutions": [], "game": game})


@app.route("/api/resolve", methods=["GET"])
def resolve_conflict():
    """Get resolution pattern for a conflict type. ?type=missing_requirement&game=skyrimse
    For AI: given conflict type, what are known resolutions and links?"""
    conflict_type = (
        (request.args.get("type") or request.args.get("conflict_type") or "").strip().lower()
    )
    game = (request.args.get("game") or DEFAULT_GAME).lower()
    if not conflict_type:
        return jsonify({"error": "type or conflict_type required"}), 400
    res = get_resolution_for_conflict(conflict_type)
    if not res:
        return jsonify({"error": f"Unknown conflict type: {conflict_type}"}), 404
    game_res = get_game_resources(game)
    return jsonify(
        {
            "conflict_type": conflict_type,
            "resolution": res,
            "game_resources": game_res,
        }
    )


def _build_next_actions(
    game: str,
    errors,
    warnings,
    info,
    plugin_limit_warning: Optional[str],
    mod_warnings_list,
    masterlist_version: Optional[str],
    game_version: Optional[str],
):
    actions = []
    err_count = len(errors or [])
    warn_count = len(warnings or [])
    info_count = len(info or [])
    if plugin_limit_warning:
        actions.append(
            {
                "id": "plugin-limit",
                "title": "Reduce plugin pressure",
                "priority": "high",
                "kind": "warning",
                "summary": plugin_limit_warning,
                "actions": [
                    {
                        "label": "Learn about ESLs",
                        "type": "link",
                        "url": "https://www.nexusmods.com/skyrimspecialedition/articles/1187",
                    },
                    {
                        "label": "Go to heaviest mods",
                        "type": "scroll",
                        "target": "system-impact-section",
                    },
                ],
            }
        )
    if err_count > 0:
        actions.append(
            {
                "id": "fix-errors",
                "title": "Fix errors first",
                "priority": "high",
                "kind": "error",
                "summary": f"{err_count} error(s) block stability. Start here before tweaking visuals or balance.",
                "actions": [
                    {"label": "Show only errors", "type": "filter", "value": "errors"},
                    {
                        "label": "Search fixes on the web (Pro)",
                        "type": "suggest",
                        "value": "search_solutions",
                    },
                ],
            }
        )
    if warn_count > 0:
        actions.append(
            {
                "id": "address-warnings",
                "title": "Work through warnings",
                "priority": "medium",
                "kind": "warning",
                "summary": f"{warn_count} warning(s) may cause crashes, missing features, or subtle bugs.",
                "actions": [
                    {"label": "Show only warnings", "type": "filter", "value": "warnings"},
                ],
            }
        )
    if err_count == 0 and warn_count == 0 and info_count == 0:
        actions.append(
            {
                "id": "looks-good",
                "title": "Looks stable — next, improve your build safely",
                "priority": "low",
                "kind": "success",
                "summary": "No issues found in the masterlist checks. Next steps: lock your load order, then add mods incrementally.",
                "actions": [
                    {
                        "label": "Build a list (generate a new setup)",
                        "type": "tab",
                        "target": "build-list",
                    },
                    {"label": "Copy share link", "type": "client", "value": "share_link"},
                ],
            }
        )
    if mod_warnings_list:
        severe = [
            w
            for w in (mod_warnings_list or [])
            if (w.get("severity") or "").lower() in ("error", "warning")
        ]
        if severe:
            actions.append(
                {
                    "id": "mod-warnings",
                    "title": "Address mod list warnings",
                    "priority": "medium",
                    "kind": "warning",
                    "summary": f"{len(severe)} warning(s) flagged for plugin limit, VRAM, or complexity.",
                    "actions": [
                        {
                            "label": "View warnings",
                            "type": "scroll",
                            "target": "mod-warnings-section",
                        },
                    ],
                }
            )
    if masterlist_version and masterlist_version != "latest":
        actions.append(
            {
                "id": "data-branch",
                "title": "Use the latest LOOT data (recommended)",
                "priority": "low",
                "kind": "info",
                "summary": f'You analyzed against branch "{masterlist_version}". Latest data usually finds more mods and rules.',
                "actions": [
                    {
                        "label": "Switch to Latest",
                        "type": "client",
                        "value": "set_masterlist_latest",
                    },
                    {"label": "Refresh data", "type": "client", "value": "refresh_masterlist"},
                ],
            }
        )
    if game_version:
        actions.append(
            {
                "id": "game-version",
                "title": "Confirm game version match",
                "priority": "low",
                "kind": "info",
                "summary": f'You selected game version "{game_version}". Keep version-consistent SKSE/F4SE/Address Library mods.',
                "actions": [
                    {"label": "Quick Start version guides", "type": "tab", "target": "quickstart"},
                ],
            }
        )
    if game:
        actions.append(
            {
                "id": "research",
                "title": "Research a mod from your list",
                "priority": "low",
                "kind": "info",
                "summary": "Use mod search to add missing requirements or validate compatibility before you install.",
                "actions": [
                    {"label": "Focus mod search", "type": "client", "value": "focus_mod_search"},
                ],
            }
        )
    return actions[:8]


@app.route("/api/analyze", methods=["POST"])
@rate_limit(RATE_LIMIT_ANALYZE, "analyze")
def analyze_mods():
    """Analyze mod list and return conflicts, suggested load order, and stats."""
    # Check if data is still loading (Priority 4B)
    if getattr(app, "_data_loading", False):
        return api_error(
            "Mod database is loading (first start). Please wait 30 seconds and try again.", 503
        )

    try:
        data = request.get_json() or {}
        if not data:
            return api_error("Invalid JSON request body", 400)

        # Validate and sanitize inputs
        mod_list_text = validate_mod_list(data.get("mod_list", ""))
        game = validate_game_id(data.get("game", DEFAULT_GAME))
        game_version = (data.get("game_version") or "").strip() or None
        masterlist_version = (data.get("masterlist_version") or "").strip() or None
        specs = data.get("specs") if isinstance(data.get("specs"), dict) else None

        mods = parse_mod_list_text(mod_list_text)
        # No minimum: 1 mod, 2 mods, or any number is allowed.
        if not mods:
            return api_error(
                "Could not parse mod list. Add one or more mods in a supported format (e.g. *ModName.esp per line).",
                400,
            )

        user_email = session.get("user_email")
        user_tier = get_user_tier(user_email) if user_email else "free"

        game_raw = (data.get("game") or DEFAULT_GAME).lower().strip()
        allowed_ids = {g["id"] for g in SUPPORTED_GAMES}
        game = game_raw if game_raw in allowed_ids else DEFAULT_GAME
        masterlist_version = (data.get("masterlist_version") or "").strip() or "latest"
        game_version = (data.get("game_version") or "").strip()
        try:
            active_parser = get_parser(game, version=masterlist_version)
        except Exception as e:
            logger.warning(f"Parser for {game} failed: {e}, using default")
            active_parser = parser

        nexus_slug = NEXUS_GAME_SLUGS.get(game, "skyrimspecialedition")
        detector = ConflictDetector(active_parser, nexus_slug=nexus_slug)
        detector.analyze_load_order(mods)
        grouped = detector.get_conflicts_by_severity()
        err_list = grouped.get("error", [])
        warn_list = grouped.get("warning", [])
        info_list = grouped.get("info", [])

        enabled_count = sum(1 for m in mods if m.enabled)
        suggested_order = detector.get_suggested_load_order(mods)
        plugin_limit_warning = None
        if enabled_count >= PLUGIN_LIMIT_WARN_THRESHOLD:
            plugin_limit_warning = (
                f"You have {enabled_count} enabled plugins. "
                f"Skyrim/FO4 cap is {PLUGIN_LIMIT} (ESLs don't count). "
                "Merging or disabling some plugins may be needed."
            )

        def _build_conflict_links(c, slug):
            """Build contextual links for a conflict (Nexus, xEdit, LOOT) + resolution from knowledge_index."""
            from urllib.parse import quote

            links = []
            base = f"https://www.nexusmods.com/games/{slug}/mods?keyword="
            if c.affected_mod:
                links.append(
                    {
                        "title": "Nexus: "
                        + (
                            c.affected_mod[:30] + "…"
                            if len(c.affected_mod) > 30
                            else c.affected_mod
                        ),
                        "url": base + quote(c.affected_mod),
                    }
                )
            related = getattr(c, "related_mod", None)
            if related and related != (c.affected_mod or ""):
                links.append(
                    {
                        "title": "Nexus: " + (related[:30] + "…" if len(related) > 30 else related),
                        "url": base + quote(related),
                    }
                )
            if c.type == "dirty_edits":
                from conflict_detector import _XEDIT_DOCS, _XEDIT_LINKS

                game_id = getattr(active_parser, "game", "skyrimse")
                _, editor_url = _XEDIT_LINKS.get(game_id, ("xEdit", _XEDIT_DOCS))
                links.append({"title": "xEdit cleaning guide", "url": _XEDIT_DOCS})
            if c.type == "load_order_violation":
                links.append({"title": "LOOT", "url": "https://loot.github.io/"})
            # Add resolution links from knowledge_index (dedupe by URL)
            seen_urls = {lnk["url"] for lnk in links}
            resolution = get_resolution_for_conflict(getattr(c, "type", "info"))
            for link in resolution.get("links") or []:
                if isinstance(link, (list, tuple)) and len(link) >= 2 and link[1] not in seen_urls:
                    seen_urls.add(link[1])
                    links.append({"title": link[0], "url": link[1]})
            return links

        def safe_conflict_dict(c):
            d = c.__dict__.copy()
            d["message"] = html.escape(str(d.get("message", "")))
            if d.get("suggested_action"):
                d["suggested_action"] = html.escape(str(d["suggested_action"]))
            d["links"] = _build_conflict_links(c, nexus_slug)
            return d

        all_visible = err_list + warn_list + info_list
        things_to_verify = _extract_things_to_verify(all_visible)
        game_name = GAME_DISPLAY_NAMES.get(game, game)

        # Refinement Cycle: Log conflicts to learn from them
        _log_conflict_stats(game, all_visible)

        masterlist_ver = getattr(active_parser, "version", "latest")

        specs = data.get("specs") or get_user_specs(user_email) or {}
        if isinstance(specs, dict):
            specs = {k: v for k, v in specs.items() if v}

        # Knowledge index: resolutions + esoteric solutions for AI
        knowledge_ctx = build_knowledge_context(
            game_id=game,
            conflicts=all_visible,
            mod_list=[m.name for m in mods if m.enabled],
            specs=specs,
            user_query=None,
        )

        # System impact + heaviest mods ranking: free for all tiers
        mod_names = [m.name for m in mods if m.enabled]
        system_impact = get_system_impact(
            mod_names=mod_names,
            enabled_count=enabled_count,
            specs=specs,
        )

        # Unified mod warnings (plugin limit, VRAM, etc.) with fix links
        mod_warnings_list = get_mod_warnings(
            mod_list_text=mod_list_text,
            mod_list=mod_names,
            game=game,
            specs=specs,
        )

        payload = {
            "success": True,
            "mod_count": len(mods),
            "enabled_count": enabled_count,
            "user_tier": user_tier,
            "game": game,
            "nexus_game_slug": NEXUS_GAME_SLUGS.get(game, "skyrimspecialedition"),
            "conflicts": {
                "errors": [safe_conflict_dict(c) for c in err_list],
                "warnings": [safe_conflict_dict(c) for c in warn_list],
                "info": [safe_conflict_dict(c) for c in info_list],
            },
            "report": detector.format_report()
            + (format_system_impact_report(system_impact) if system_impact else ""),
            "summary": {
                "total": len(err_list) + len(warn_list) + len(info_list),
                "errors": len(err_list),
                "warnings": len(warn_list),
                "info": len(info_list),
            },
            "suggested_load_order": suggested_order,
            "plugin_limit_warning": plugin_limit_warning,
            "data_source": f"LOOT masterlist ({game_name})",
            "masterlist_version": masterlist_ver,
            "things_to_verify": things_to_verify,
            "ai_context": (
                detector.format_report_for_ai(
                    game_name=game_name, nexus_slug=nexus_slug, specs=specs
                )
                + (("\n\n" + format_system_impact_for_ai(system_impact)) if system_impact else "")
                + format_knowledge_for_ai(knowledge_ctx)
            ),
            "specs": specs,
            "system_impact": system_impact,
            "knowledge": knowledge_ctx,
            "mod_warnings": mod_warnings_list,
            # HAL+JSON style links for the analysis itself
            "_links": {
                "self": {"href": f"/api/analyze?game={game}", "title": "Analyze this mod list"},
                "search": {
                    "href": f"/api/search?game={game}&limit=10",
                    "title": "Search mods for this game",
                },
                "build_list": {
                    "href": "/api/build-list",
                    "title": "Build a mod list for this game",
                },
                "save_list": {"href": "/api/list-preferences", "title": "Save this mod list (Pro)"},
                "solutions": {
                    "href": f"/api/search-solutions?game={game}",
                    "title": "Search for solutions to conflicts",
                },
                "community": {
                    "href": "/api/community/posts?game=" + game,
                    "title": "Community posts for this game",
                },
            },
        }
        payload["next_actions"] = _build_next_actions(
            game=game,
            errors=payload["conflicts"]["errors"],
            warnings=payload["conflicts"]["warnings"],
            info=payload["conflicts"]["info"],
            plugin_limit_warning=plugin_limit_warning,
            mod_warnings_list=mod_warnings_list,
            masterlist_version=masterlist_ver,
            game_version=game_version or None,
        )
        if game_version:
            payload["game_version"] = game_version
            version_info = get_version_info(game, game_version)
            if version_info:
                payload["game_version_info"] = version_info
            version_warn = get_version_warning(game, game_version)
            if version_warn:
                payload["game_version_warning"] = version_warn
        track_activity(
            "analyze",
            {
                "game": game,
                "mod_count": len(mods),
                "enabled_count": enabled_count,
                "errors": len(err_list),
                "warnings": len(warn_list),
                "info": len(info_list),
            },
            user_email,
        )
        return jsonify(payload)
    except Exception as e:
        logger.error(f"Analysis error: {str(e)}")
        return api_error("Analysis failed. Please try again or contact support.", 500)


def _get_api_key_from_request():
    """Extract API key from Authorization: Bearer <key> or X-API-Key: <key>. Returns raw key or None."""
    auth = request.headers.get("Authorization")
    if auth and auth.startswith("Bearer "):
        return auth[7:].strip()
    return request.headers.get("X-API-Key", "").strip() or None


@app.route("/api/v1/analyze", methods=["POST"])
@rate_limit(RATE_LIMIT_ANALYZE, "analyze")
def api_v1_analyze():
    """Developer API: analyze mod list with API key. Returns shorter, filtered JSON (no report HTML). Auth: Authorization: Bearer <key> or X-API-Key: <key>."""
    raw_key = _get_api_key_from_request()
    user_email = api_key_lookup(raw_key) if raw_key else None
    if not user_email:
        return api_error(
            "Invalid or missing API key. Use Authorization: Bearer <key> or X-API-Key header.", 401
        )
    try:
        data = request.get_json() or {}
        mod_list_text = data.get("mod_list")
        if not mod_list_text:
            return api_error("mod_list required", 400)
        if len(mod_list_text) > MAX_INPUT_SIZE:
            return api_error(f"mod_list too large (max {MAX_INPUT_SIZE} chars)", 413)
        mods = parse_mod_list_text(mod_list_text)
        if not mods:
            return api_error("Could not parse mod list", 400)
        game_raw = (data.get("game") or DEFAULT_GAME).lower().strip()
        allowed_ids = {g["id"] for g in SUPPORTED_GAMES}
        game = game_raw if game_raw in allowed_ids else DEFAULT_GAME
        masterlist_version = (data.get("masterlist_version") or "").strip() or "latest"
        try:
            active_parser = get_parser(game, version=masterlist_version)
        except Exception:
            active_parser = parser
        nexus_slug = NEXUS_GAME_SLUGS.get(game, "skyrimspecialedition")
        detector = ConflictDetector(active_parser, nexus_slug=nexus_slug)
        detector.analyze_load_order(mods)
        grouped = detector.get_conflicts_by_severity()
        err_list = grouped.get("error", [])
        warn_list = grouped.get("warning", [])
        info_list = grouped.get("info", [])
        enabled_count = sum(1 for m in mods if m.enabled)

        def short_conflict(c):
            return {
                "severity": c.severity,
                "type": getattr(c, "type", "unknown"),
                "message": str(c.message or ""),
                "affected_mod": c.affected_mod,
                "suggested_action": c.suggested_action,
            }

        payload = {
            "game": game,
            "mod_count": len(mods),
            "enabled_count": enabled_count,
            "conflicts": [short_conflict(c) for c in err_list + warn_list + info_list],
            "summary": {
                "errors": len(err_list),
                "warnings": len(warn_list),
                "info": len(info_list),
                "total": len(err_list) + len(warn_list) + len(info_list),
            },
        }
        return jsonify(payload)
    except Exception as e:
        logger.exception("API v1 analyze error: %s", e)
        return api_error("Analysis failed", 500)


@app.route("/payment-success")
def payment_success():
    """Handle successful payment return."""
    if not PAYMENTS_ENABLED:
        return redirect(url_for("index"))

    session_id = request.args.get("session_id")
    if not session_id:
        return redirect(url_for("index", error="missing_session"))

    try:
        checkout_session = stripe.checkout.Session.retrieve(session_id)

        if checkout_session.payment_status == "paid":
            # Retrieve customer and email
            customer = stripe.Customer.retrieve(checkout_session.customer)
            email = customer.email.lower()
            purchased_tier = _tier_from_checkout_session(checkout_session)

            # Activate user
            set_user_tier(
                email=email,
                tier=purchased_tier,
                customer_id=checkout_session.customer,
                subscription_id=checkout_session.subscription,
            )

            # Log user in: create session and set cookie
            sess_token, max_age = session_create(
                email, remember_me=True, user_agent=request.headers.get("User-Agent")
            )
            resp = make_response(
                render_template("success.html", email=email, tier=tier_label(purchased_tier))
            )
            if sess_token:
                resp.set_cookie(
                    SESSION_COOKIE_NAME,
                    sess_token,
                    max_age=max_age,
                    httponly=True,
                    secure=app.config["SESSION_COOKIE_SECURE"],
                    samesite=app.config["SESSION_COOKIE_SAMESITE"],
                )
            logger.info(f"Payment success for {_redact_email(email)}")
            return resp
        else:
            return redirect(url_for("index", error="payment_incomplete"))

    except stripe.error.StripeError as e:
        logger.error(f"Stripe verification error: {str(e)}")
        return redirect(url_for("index", error="stripe_error"))
    except Exception as e:
        logger.error(f"Payment verification error: {str(e)}")
        return redirect(url_for("index", error="verification_failed"))


@app.route("/webhook", methods=["POST"])
def webhook():
    """Stripe webhook endpoint for subscription events."""
    if not PAYMENTS_ENABLED:
        return "", 200

    payload = request.data
    sig_header = request.headers.get("Stripe-Signature")

    # Verify webhook signature
    try:
        event = stripe.Webhook.construct_event(payload, sig_header, stripe_webhook_secret)
    except ValueError:
        logger.warning("Webhook invalid payload")
        return "", 400
    except stripe.error.SignatureVerificationError:
        logger.warning("Webhook signature verification failed")
        return "", 400

    event_type = event["type"]
    event_data = event["data"]["object"]

    try:
        if event_type == "invoice.paid":
            # Recurring payment success
            customer = stripe.Customer.retrieve(event_data["customer"])
            email = customer.email.lower()
            resolved_tier = _tier_from_subscription(event_data.get("subscription"))
            set_user_tier(
                email=email,
                tier=resolved_tier,
                customer_id=event_data["customer"],
                subscription_id=event_data["subscription"],
            )
            logger.info(f"Invoice paid for {_redact_email(email)}")

        elif event_type == "invoice.payment_failed":
            # Payment failed - downgrade
            customer = stripe.Customer.retrieve(event_data["customer"])
            email = customer.email.lower()
            set_user_tier(email=email, tier="free")
            logger.info(f"Payment failed for {_redact_email(email)} - downgraded to free")

        elif event_type == "customer.subscription.deleted":
            # Subscription cancelled
            customer = stripe.Customer.retrieve(event_data["customer"])
            email = customer.email.lower()
            set_user_tier(email=email, tier="free")
            logger.info(f"Subscription deleted for {_redact_email(email)} - downgraded to free")

        elif event_type == "checkout.session.completed":
            # Initial checkout success (backup for direct verification)
            if event_data["payment_status"] == "paid":
                customer = stripe.Customer.retrieve(event_data["customer"])
                email = customer.email.lower()
                resolved_tier = _tier_from_checkout_session(event_data)
                set_user_tier(
                    email=email,
                    tier=resolved_tier,
                    customer_id=event_data["customer"],
                    subscription_id=event_data.get("subscription"),
                )
                logger.info(f"Checkout completed for {_redact_email(email)}")

        return "", 200

    except Exception as e:
        logger.error(f"Webhook processing error for {event_type}: {str(e)}")
        return "", 500


_PROBLEM_KEYWORDS = frozenset(
    [
        "ctd",
        "crash",
        "fix",
        "broken",
        "not working",
        "help",
        "issue",
        "problem",
        "infinite loading",
        "ils",
        "purple",
        "texture",
        "t-pose",
        "tpose",
        "error",
        "stuck",
        "freeze",
        "black screen",
        "missing",
        "won't load",
    ]
)


def _log_conflict_stats(game, conflicts):
    """Log conflict occurrences to build a predictive database (The 'Bins')."""
    if not conflicts:
        return
    try:
        db = get_db()
        for c in conflicts:
            # Handle both dict (from API) and object (from detector)
            if isinstance(c, dict):
                mod_a = c.get('affected_mod')
                mod_b = c.get('related_mod')
                c_type = c.get('type')
            else:
                mod_a = getattr(c, 'affected_mod', None)
                mod_b = getattr(c, 'related_mod', None)
                c_type = getattr(c, 'type', None)

            if not mod_a:
                continue
            mod_b = mod_b or ''
            c_type = c_type or 'unknown'

            db.execute("""
                INSERT INTO conflict_stats (game, mod_a, mod_b, conflict_type, last_seen, occurrence_count)
                VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP, 1)
                ON CONFLICT(game, mod_a, mod_b, conflict_type)
                DO UPDATE SET occurrence_count = occurrence_count + 1, last_seen = CURRENT_TIMESTAMP
            """, (game, mod_a, mod_b, c_type))
        db.commit()
    except Exception as e:
        logger.debug(f"Failed to log conflict stats: {e}")


def _get_deep_mod_context(game, message, user_mod_list):
    """Retrieve deep LOOT metadata for mods mentioned in chat (The 'Deep Dive')."""
    if not message:
        return ""
    p = get_parser(game)
    mentioned = set()
    msg_lower = message.lower()

    # Check user's active list
    for m in user_mod_list:
        if m.lower() in msg_lower:
            mentioned.add(m)

    info = []
    for m in mentioned:
        meta = p.get_mod_info(m)
        if meta:
            tags = ", ".join(meta.tags) if meta.tags else "None"
            msgs = " ".join([msg.get('content', '') for msg in meta.messages])
            # Provide raw technical data that generic LLMs usually lack
            info.append(f"Deep Data for {m}:\n- Tags: {tags}\n- LOOT Messages: {msgs or 'None'}\n- CRC: {meta.crc or 'N/A'}")

    return "\n\n".join(info)


def _get_community_intelligence(game, user_mod_list):
    """Query the 'Intimate Database' for community conflict stats involving these mods."""
    if not user_mod_list:
        return ""
    try:
        db = get_db()
        # Sanitize and limit mod list for SQL query
        safe_mods = list(set(user_mod_list))[:100]
        if not safe_mods:
            return ""

        placeholders = ','.join(['?'] * len(safe_mods))
        sql = f"""
            SELECT mod_a, mod_b, conflict_type, occurrence_count
            FROM conflict_stats
            WHERE game = ?
            AND (mod_a IN ({placeholders}) OR mod_b IN ({placeholders}))
            AND occurrence_count > 1
            ORDER BY occurrence_count DESC
            LIMIT 5
        """
        params = [game] + safe_mods + safe_mods
        rows = db.execute(sql, params).fetchall()

        if not rows:
            return ""

        info = []
        for r in rows:
            mod_b_str = f" + {r['mod_b']}" if r['mod_b'] else ""
            info.append(f"- {r['mod_a']}{mod_b_str} -> {r['conflict_type']} (Frequency: {r['occurrence_count']})")

        return "Community Patterns (The Bins):\n" + "\n".join(info)
    except Exception as e:
        logger.debug(f"Community intelligence lookup failed: {e}")
        return ""


@app.route("/api/chat", methods=["POST"])
@rate_limit(RATE_LIMIT_ANALYZE, "chat")
def chat():
    """Pro: chat about your load order / conflicts. Key from LLM_API_KEY env only."""
    if not AI_CHAT_ENABLED:
        return jsonify(
            {"error": "AI chat is not configured. Set LLM_API_KEY in your environment."}
        ), 503
    user_email = session.get("user_email")
    data = request.get_json() or {}
    message = (data.get("message") or "").strip()
    if not message:
        return jsonify({"error": "Message is required."}), 400
    context = (data.get("context") or "").strip()
    page_context = (data.get("page_context") or "").strip()
    game = (data.get("game") or DEFAULT_GAME).lower()
    # Fetch scattered web solutions when user asks about a problem
    web_solutions = []
    msg_lower = message.lower()
    if any(kw in msg_lower for kw in _PROBLEM_KEYWORDS):
        try:
            from web_search import search_solutions_web

            game_obj = next((g for g in SUPPORTED_GAMES if g["id"] == game), None)
            game_name = game_obj["name"] if game_obj else "Skyrim"
            web_solutions = search_solutions_web(
                query=message[:80], game_display_name=game_name, max_results=5
            )
        except Exception as e:
            logger.debug("Web solutions fetch failed: %s", e)

    # Build profile context
    profile_summary = ""
    if user_email:
        specs = get_user_specs(user_email)
        saved_lists = list_user_saved_lists(user_email)
        profile_summary = f"\nUser Profile:\n- Email: {user_email}\n"
        if specs:
            profile_summary += f"- Specs: {json.dumps(specs)}\n"
        if saved_lists:
            profile_summary += f"- Saved Lists: {len(saved_lists)} lists ({', '.join(item['name'] for item in saved_lists[:3])}...)\n"

    # Deep Dive: Inject intimate database knowledge for mentioned mods
    mod_list = data.get("mod_list") or []
    deep_context = _get_deep_mod_context(game, message, mod_list)
    community_context = _get_community_intelligence(game, mod_list)

    system = (
        "You are the SkyModderAI assistant. Your task: help the user fix their load order and feel confident doing it. "
        "Ease them into the process—acknowledge what they're dealing with, then guide step by step. "
        "You help with Skyrim, Fallout, and other Bethesda game modding: load order, LOOT, "
        "conflicts, compatibility, and performance. Be concise and practical. The user's context includes "
        "their game, mod list analysis, conflict types (missing_requirement, incompatible, "
        "load_order_violation, dirty_edits, patch_available), and when available: System Impact "
        "(complexity, estimated VRAM, heavy mods, recommendations). Use the structured data to give "
        "specific, actionable advice. For performance questions, reference their specs and heavy mods. "
        "Suggest Nexus, xEdit, or LOOT when relevant. Don't make up mod names or links. "
        "When community solutions are provided, you may cite them to help the user find scattered fixes. "
        "When Top mod picks are provided (Utility, Design, Fun, Environmental), you may suggest them "
        "when the user asks for recommendations—e.g. 'For design, try X' or 'A great utility pick is Y'. "
        "You have access to the user's profile, page content, and deep LOOT metadata. "
        "Tailor your advice specifically to their mod list and specs. Be predictive: anticipate issues based on the community patterns."
        f"{profile_summary}"
    )
    parts = []
    if context:
        from pruning import prune_input_context

        pruned, _ = prune_input_context(context, user_message=message, max_chars=10000)
        parts.append(f"Context from the user's last SkyModderAI analysis:\n\n{pruned}")
    if page_context:
        parts.append(f"Current Page Content (what the user is looking at):\n\n{page_context[:5000]}")
    if deep_context:
        parts.append(f"Deep LOOT Metadata (Intimate Database):\n{deep_context}")
    if community_context:
        parts.append(community_context)

    if web_solutions:
        sol_block = "Community solutions (from Reddit/Nexus):\n" + "\n".join(
            f"- [{s.get('title', '')}]({s.get('url', '')}): {(s.get('snippet') or '')[:150]}..."
            for s in web_solutions[:5]
        )
        parts.append(sol_block)
    # Pre-fetch recommendations + top picks for AI context and response
    rec_payload = {"recommendations": [], "top_picks": {}}
    try:
        if not mod_list and context:
            import re

            mod_list = re.findall(r"\*\*([^*]+\.(?:esp|esm|esl))\*\*", context)
        game_for_rec = (data.get("game") or DEFAULT_GAME).lower()
        nexus_slug = NEXUS_GAME_SLUGS.get(game_for_rec, "skyrimspecialedition")
        p = get_parser(game_for_rec)
        rec_payload = get_recommendations_for_ai(
            p, mod_list, game_for_rec, nexus_slug, limit=10, top_picks_per_category=2
        )
    except Exception:
        pass
    top_picks_for_context = rec_payload.get("top_picks", {})
    if top_picks_for_context:
        picks_block = "Top mod picks for user's setup (you may suggest these when relevant):\n"
        for cat, items in top_picks_for_context.items():
            if items:
                names = [m.get("name", "") for m in items if m.get("name")]
                if names:
                    picks_block += f"  {cat.title()}: {', '.join(names)}\n"
        parts.append(picks_block)
    parts.append(f"User question: {message}")
    user_content = "\n\n".join(parts)
    try:
        client = get_ai_client()
        r = client.chat.completions.create(
            model=LLM_MODEL,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user_content},
            ],
            max_tokens=1024,
            temperature=0.3,
        )
        reply = (r.choices[0].message.content or "").strip()
        # Output pruning: distilled version for Fix Guide (keeps full reply for chat)
        from pruning import prune_output_for_fix_guide

        reply_for_fix_guide = prune_output_for_fix_guide(reply, max_bullets=8)
        recommended_mods = rec_payload.get("recommendations", [])[:8]
        top_picks = rec_payload.get("top_picks", {})
        track_activity(
            "chat",
            {"game": game, "message_len": len(message), "web_solutions": len(web_solutions)},
            user_email,
        )
        return jsonify(
            {
                "reply": reply,
                "reply_for_fix_guide": reply_for_fix_guide,
                "recommended_mods": recommended_mods,
                "top_picks": top_picks,
            }
        )
    except openai.APIError as e:
        logger.warning(f"OpenAI API error: {e}")
        return jsonify({"error": "AI is temporarily unavailable. Try again in a moment."}), 502
    except Exception:
        logger.exception("Chat error")
        return jsonify({"error": "Something went wrong. Please try again."}), 500


@app.route("/api/scan-game-folder", methods=["POST"])
@rate_limit(RATE_LIMIT_ANALYZE, "scan-folder")
def scan_game_folder():
    """Pro: AI scans user's game folder (file tree + key files) for issues beyond Mod Organizer."""
    if not AI_CHAT_ENABLED:
        return jsonify({"error": "AI is not configured. Set OPENAI_API_KEY."}), 503
    user_email = session.get("user_email")
    data = request.get_json() or {}
    game = (data.get("game") or DEFAULT_GAME).lower()
    tree = (data.get("tree") or "").strip()
    key_files = data.get("keyFilesContent") or data.get("key_files_content") or {}
    plugins = data.get("plugins") or []
    file_count = data.get("fileCount", 0)
    if not tree and not key_files and not plugins:
        return jsonify({"error": "No folder data received. Select or drop your game folder."}), 400
    game_name = next((g["name"] for g in SUPPORTED_GAMES if g["id"] == game), "Skyrim")
    from pruning import prune_game_folder_context

    tree_pruned, key_files_pruned, _ = prune_game_folder_context(
        tree, key_files, plugins, max_tree_chars=5000, max_file_chars=3000
    )
    key_block = []
    for path, content in key_files_pruned.items():
        key_block.append(f"--- {path} ---\n{(content or '')}")
    context = f"""User scanned their {game_name} game folder. Analyze for issues beyond load order.

File count: {file_count}
Plugins found in Data/: {", ".join(plugins[:80])}{"..." if len(plugins) > 80 else ""}

Folder structure:
{tree_pruned}

Key config files:
{chr(10).join(key_block)}
"""
    system = (
        "You are the SkyModderAI assistant. The user has shared their game folder structure and key files. "
        "Analyze for issues that Mod Organizer / Vortex might not catch: "
        "direct overwrites in Data/, unusual file placement, missing expected files, "
        "conflicting loose files, plugins.txt vs actual Data/ mismatch, MO2 vs Vortex deployment quirks. "
        "Be concise. Use bullet points. If everything looks fine, say so briefly. "
        "Don't make up mod names. Suggest xEdit, LOOT, or Nexus when relevant."
    )
    try:
        client = get_ai_client()
        r = client.chat.completions.create(
            model=LLM_MODEL,
            messages=[{"role": "system", "content": system}, {"role": "user", "content": context}],
            max_tokens=1024,
            temperature=0.2,
        )
        report = (r.choices[0].message.content or "").strip()
        return jsonify({"report": report, "findings": report, "plugins_found": plugins[:255]})
    except openai.APIError as e:
        logger.warning(f"OpenAI API error (scan-game-folder): {e}")
        return jsonify({"error": "AI is temporarily unavailable. Try again in a moment."}), 502
    except Exception:
        logger.exception("Scan game folder error")
        return jsonify({"error": "Something went wrong. Please try again."}), 500


# -------------------------------------------------------------------
# Dev Tools (Pro) — AI code analysis for mod authors
# -------------------------------------------------------------------
_DEV_RELEVANT_EXT = (
    ".psc",
    ".ini",
    ".json",
    ".toml",
    ".yaml",
    ".yml",
    ".txt",
    ".md",
)  # text only; .esp/.esm/.esl are binary
_DEV_RELEVANT_NAMES = ("readme", "license", "changelog", "fomod", "meta.ini", "moduleconfig")


def _parse_github_url(url):
    """Extract owner/repo from GitHub URL. Returns (owner, repo) or None."""
    url = (url or "").strip()
    if not url.startswith(("http://", "https://")):
        return None
    try:
        from urllib.parse import urlparse

        parsed = urlparse(url)
        if "github.com" not in parsed.netloc.lower():
            return None
        parts = [p for p in parsed.path.strip("/").split("/") if p]
        if len(parts) >= 2 and parts[0] and parts[1]:
            return (parts[0], parts[1].replace(".git", ""))
    except Exception:
        pass
    return None


def _fetch_github_repo(owner, repo, max_files=25, max_bytes=400000):
    """Fetch relevant text files from a public GitHub repo. Returns {path: content}."""
    headers = {"Accept": "application/vnd.github.v3+json"}
    token = os.environ.get("GITHUB_TOKEN", "").strip()
    if token:
        headers["Authorization"] = f"token {token}"
    base = f"https://api.github.com/repos/{owner}/{repo}"
    files = {}
    plugin_paths = []
    total_bytes = 0

    session = requests.Session()
    session.headers.update(headers)

    def is_relevant(name):
        n = name.lower()
        if any(n.endswith(e) for e in _DEV_RELEVANT_EXT):
            return True
        if any(r in n for r in _DEV_RELEVANT_NAMES):
            return True
        return False

    def is_plugin(name):
        return name.lower().endswith((".esp", ".esm", ".esl"))

    def fetch_dir(path, depth=0):
        nonlocal total_bytes
        if depth > 3 or len(files) >= max_files or total_bytes >= max_bytes:
            return
        url = f"{base}/contents/{path}" if path else f"{base}/contents/"
        try:
            r = session.get(url, timeout=10)
            r.raise_for_status()
            items = r.json()
            if not isinstance(items, list):
                items = [items]
            for item in items:
                if len(files) >= max_files or total_bytes >= max_bytes:
                    return
                name = item.get("name") or ""
                full_path = item.get("path") or (f"{path}/{name}".lstrip("/") if path else name)
                if item.get("type") == "dir":
                    fetch_dir(full_path, depth + 1)
                elif item.get("type") == "file":
                    if is_plugin(name):
                        plugin_paths.append(full_path)
                    elif is_relevant(name):
                        dl = item.get("download_url")
                        if dl:
                            try:
                                rr = session.get(dl, timeout=8)
                                if rr.ok:
                                    content = rr.text[:15000]
                                    files[full_path] = content
                                    total_bytes += len(content)
                            except Exception:
                                pass
        except requests.RequestException:
            pass

    try:
        fetch_dir("")
    finally:
        session.close()

    if plugin_paths:
        files["_plugins_list"] = "Plugin files (binary): " + ", ".join(plugin_paths[:30])
    return files


@app.route("/api/dev-analyze", methods=["POST"])
@rate_limit(RATE_LIMIT_ANALYZE, "dev-analyze")
def api_dev_analyze():
    """Pro: AI analyzes mod project (GitHub repo URL or uploaded files) for runtime compatibility."""
    if not AI_CHAT_ENABLED:
        return jsonify({"error": "AI is not configured. Set OPENAI_API_KEY."}), 503
    user_email = session.get("user_email")

    data = request.get_json() or {}
    repo_url = (data.get("repo_url") or data.get("repoUrl") or "").strip()
    files_data = data.get("files") or []
    game = (data.get("game") or "skyrimse").lower()
    game_name = next((g["name"] for g in SUPPORTED_GAMES if g["id"] == game), "Skyrim SE")

    files_content = {}
    if repo_url:
        parsed = _parse_github_url(repo_url)
        if not parsed:
            return jsonify({"error": "Invalid GitHub URL. Use https://github.com/owner/repo"}), 400
        try:
            files_content = _fetch_github_repo(parsed[0], parsed[1])
        except Exception as e:
            logger.warning("Dev analyze GitHub fetch: %s", e)
            return jsonify({"error": "Could not fetch repo. Is it public?"}), 502
        if not files_content:
            return jsonify(
                {"error": "No relevant files found (look for .psc, .esp, .ini, README, etc.)"}
            ), 400
    else:
        for f in files_data[:30]:
            path = (f.get("path") or f.get("name") or "file").strip()
            content = f.get("content") or ""
            if isinstance(content, str) and len(content) < 50000:
                files_content[path] = content[:15000]
        if not files_content:
            return jsonify({"error": "No files provided. Paste a repo URL or upload files."}), 400

    context_parts = [f"Mod project for {game_name}. Analyze for runtime compatibility.\n"]
    for path, content in list(files_content.items())[:20]:
        context_parts.append(f"\n--- {path} ---\n{(content or '')[:8000]}")

    context = "\n".join(context_parts)[:50000]
    system = (
        "You are the SkyModderAI dev assistant. The user has shared their mod project (Papyrus scripts, plugins, configs). "
        "Give an intimate dev report: Will it likely run? What could break? What to fix first? "
        "Cover: missing dependencies (SKSE, F4SE, etc.), common Papyrus pitfalls, plugin structure, version compatibility, "
        "INI/config issues, missing properties, race conditions. Be specific and actionable. "
        "Use Markdown headers (##, ###) for sections and bullet points for lists. "
        "If the project looks solid, say so and note any minor improvements. Don't make up errors."
    )
    try:
        client = get_ai_client()
        r = client.chat.completions.create(
            model=LLM_MODEL,
            messages=[{"role": "system", "content": system}, {"role": "user", "content": context}],
            max_tokens=1500,
            temperature=0.2,
        )
        report = (r.choices[0].message.content or "").strip()
        track_activity(
            "dev_analyze",
            {"game": game, "files_analyzed": len(files_content), "repo_mode": bool(repo_url)},
            user_email,
        )
        return jsonify({"report": report, "files_analyzed": len(files_content)})
    except openai.APIError as e:
        logger.warning("OpenAI API error (dev-analyze): %s", e)
        return jsonify({"error": "AI is temporarily unavailable. Try again in a moment."}), 502
    except Exception:
        logger.exception("Dev analyze error")
        return jsonify({"error": "Something went wrong. Please try again."}), 500


@app.route("/api/dev-loop/suggest", methods=["POST"])
@rate_limit(RATE_LIMIT_API, "dev-loop")
def api_dev_loop_suggest():
    """
    Paid dev companion loop:
    - suggest new mod features
    - suggest performance/stability optimizations
    - explicitly recommend "idle" when further changes likely hurt stability
    """
    user_email = session.get("user_email")

    data = request.get_json() or {}
    game = (data.get("game") or DEFAULT_GAME).lower()
    if game not in {g["id"] for g in SUPPORTED_GAMES}:
        game = DEFAULT_GAME
    objective = (data.get("objective") or "new feature ideas with stable runtime").strip()[:300]
    playstyle = (data.get("playstyle") or "balanced").strip()[:160]
    signals = data.get("signals") if isinstance(data.get("signals"), dict) else {}

    def _to_int(v, default=0):
        try:
            return int(v)
        except Exception:
            return default

    def _to_float(v, default=None):
        try:
            return float(v)
        except Exception:
            return default

    fps_avg = _to_float(signals.get("fps_avg"))
    crashes = _to_int(signals.get("crashes"), 0)
    stutter = _to_int(signals.get("stutter_events"), 0)
    enjoyment = _to_int(signals.get("enjoyment_score"), 0)

    feature_ideas_map = {
        "skyrimse": [
            "Dynamic NPC routines with low-frequency update ticks and state caching.",
            "Contextual companion banter triggers backed by event throttling.",
            "Lightweight weather-reactive ambient encounters with fallback rules.",
        ],
        "fallout4": [
            "Settlement QoL automation with explicit script budget caps.",
            "Companion affinity events that debounce repeated triggers.",
            "Damage feedback clarity mod with INI-tunable thresholds.",
        ],
        "starfield": [
            "Ship-combat readability overlay tuned for performance-first HUD updates.",
            "Faction mission enhancer with minimal event listener footprint.",
            "Companion dialogue micro-reactivity with strict cooldown windows.",
        ],
    }
    feature_ideas = feature_ideas_map.get(game, feature_ideas_map.get("skyrimse", []))

    perf_actions = []
    if crashes > 0:
        perf_actions.append(
            "Prioritize crash triage: reduce script-heavy features and verify dependency versions first."
        )
    if fps_avg is not None and fps_avg < 55:
        perf_actions.append(
            "Switch to balanced/performance profile and reduce high-VRAM textures before adding new scripted systems."
        )
    if stutter > 6:
        perf_actions.append(
            "Lower script update frequency and batch expensive events to reduce frametime spikes."
        )
    if not perf_actions:
        perf_actions.append(
            "Keep current optimization profile and add only one feature change per run for clean A/B verification."
        )

    should_idle = (
        fps_avg is not None and fps_avg >= 60 and crashes == 0 and stutter <= 3 and enjoyment >= 8
    )
    idle_conclusion = (
        "Recommendation: go idle. Current run quality is strong; additional changes now are more likely to add instability than user value."
        if should_idle
        else "Recommendation: continue iterating with one controlled change per run."
    )

    safety = {
        "warning": "Outside-sandbox operations must always request explicit user permission first.",
        "policy": "No BIOS/UEFI, firmware, registry hive, kernel, or boot modifications. Ever.",
        "sandbox_first": True,
    }

    response = {
        "success": True,
        "game": game,
        "objective": objective,
        "playstyle": playstyle,
        "feature_ideas": feature_ideas,
        "optimization_actions": perf_actions,
        "idle_recommended": should_idle,
        "idle_conclusion": idle_conclusion,
        "safety": safety,
    }
    track_activity(
        "dev_loop_suggest",
        {"game": game, "idle_recommended": should_idle, "has_signals": bool(signals)},
        user_email,
    )
    return jsonify(response)


@app.route("/api/check-tier", methods=["GET"])
def check_tier():
    """Return current user's tier, email, and feature flags."""
    user_email = session.get("user_email")
    tier = get_user_tier(user_email)
    specs = get_user_specs(user_email) if user_email else None
    return jsonify(
        {
            "tier": tier,
            "tier_label": tier_label(tier),
            "email": user_email,
            "payments_enabled": PAYMENTS_ENABLED,
            "ai_chat_enabled": AI_CHAT_ENABLED,
            "has_paid_access": has_paid_access(tier),
            "is_openclaw_tier": is_openclaw_tier(tier),
            "openclaw_enabled": OPENCLAW_ENABLED,
            "openclaw_checkout_available": bool(stripe_openclaw_price_id),
            "specs": specs,
        }
    )


@app.route("/api/feedback", methods=["POST"])
@rate_limit(RATE_LIMIT_API, "feedback")
def api_feedback_submit():
    """Capture user feedback, complaints, and feature requests."""
    data = request.get_json() or {}
    kind = (data.get("type") or "feedback").strip().lower()
    category = (data.get("category") or "general").strip().lower()
    content = (data.get("content") or "").strip()
    if kind not in ("bug", "feature", "complaint", "praise", "question", "feedback"):
        kind = "feedback"
    if category not in (
        "analysis",
        "community",
        "ui",
        "performance",
        "billing",
        "devtools",
        "other",
        "general",
    ):
        category = "general"
    if len(content) < 5 or len(content) > 3000:
        return api_error("Feedback must be 5-3000 characters.", 400)
    context_obj = data.get("context") if isinstance(data.get("context"), dict) else {}
    context_obj.update(
        {
            "path": request.path,
            "user_agent": (request.headers.get("User-Agent") or "")[:240],
        }
    )
    try:
        db = get_db()
        db.execute(
            """
            INSERT INTO user_feedback (user_email, type, category, content, context_json)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                (session.get("user_email") or "").lower() or None,
                kind,
                category,
                content,
                json.dumps(context_obj, ensure_ascii=True)[:3000],
            ),
        )
        db.commit()
        track_activity(
            "feedback_submit", {"type": kind, "category": category}, session.get("user_email")
        )
        return jsonify({"success": True, "message": "Thanks. Your feedback is in the queue."})
    except Exception as e:
        logger.exception("Feedback submit failed: %s", e)
        return api_error("Could not submit feedback right now.", 500)


@app.route("/api/activity/track", methods=["POST"])
@rate_limit(RATE_LIMIT_API, "activity")
def api_activity_track():
    """Optional frontend activity tracker for UX events not visible server-side."""
    data = request.get_json() or {}
    event_type = (data.get("event_type") or "").strip().lower()
    if not event_type or len(event_type) > 64:
        return api_error("event_type required.", 400)
    event_data = data.get("event_data") if isinstance(data.get("event_data"), dict) else {}
    track_activity(event_type, event_data, session.get("user_email"))
    return jsonify({"success": True})


@app.route("/api/satisfaction/survey", methods=["POST"])
@rate_limit(RATE_LIMIT_API, "satisfaction")
def api_satisfaction_survey():
    """Capture quick post-analysis helpfulness score."""
    data = request.get_json() or {}
    try:
        rating = int(data.get("rating"))
    except (TypeError, ValueError):
        return api_error("rating must be an integer between 1 and 5.", 400)
    if rating < 1 or rating > 5:
        return api_error("rating must be an integer between 1 and 5.", 400)
    feedback_text = (data.get("feedback_text") or "").strip()[:1500]
    context_obj = data.get("context") if isinstance(data.get("context"), dict) else {}
    try:
        db = get_db()
        db.execute(
            """
            INSERT INTO satisfaction_surveys (user_email, rating, feedback_text, context_json)
            VALUES (?, ?, ?, ?)
            """,
            (
                (session.get("user_email") or "").lower() or None,
                rating,
                feedback_text,
                json.dumps(context_obj, ensure_ascii=True)[:2000],
            ),
        )
        db.commit()
        track_activity("satisfaction_submit", {"rating": rating}, session.get("user_email"))
        return jsonify({"success": True})
    except Exception as e:
        logger.exception("Satisfaction submit failed: %s", e)
        return api_error("Could not submit survey right now.", 500)


@app.route("/api/community/reports", methods=["POST"])
@login_required_api
@rate_limit(RATE_LIMIT_API, "community")
def api_community_report():
    """Report a post or reply for moderation review."""
    data = request.get_json() or {}
    post_id = data.get("post_id")
    reply_id = data.get("reply_id")
    reason = (data.get("reason") or "").strip().lower()
    details = (data.get("details") or "").strip()
    if not post_id and not reply_id:
        return api_error("post_id or reply_id is required.", 400)
    if reason not in ("spam", "abuse", "off_topic", "illegal", "other"):
        reason = "other"
    try:
        db = get_db()
        db.execute(
            """
            INSERT INTO community_reports (post_id, reply_id, reporter_email, reason, details)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                int(post_id) if post_id else None,
                int(reply_id) if reply_id else None,
                session["user_email"].lower(),
                reason,
                details[:1200],
            ),
        )
        db.commit()
        track_activity(
            "community_report",
            {"post_id": post_id, "reply_id": reply_id, "reason": reason},
            session.get("user_email"),
        )
        return jsonify({"success": True})
    except Exception as e:
        logger.exception("Community report failed: %s", e)
        return api_error("Could not submit report right now.", 500)


@app.route("/api/community/health", methods=["GET"])
def api_community_health():
    """Public community health pulse for transparency and trust."""
    try:
        db = get_db()
        posts_7d = (
            db.execute(
                "SELECT COUNT(*) FROM community_posts WHERE moderated = 0 AND created_at >= datetime('now', '-7 days')"
            ).fetchone()[0]
            or 0
        )
        replies_7d = (
            db.execute(
                "SELECT COUNT(*) FROM community_replies WHERE moderated = 0 AND created_at >= datetime('now', '-7 days')"
            ).fetchone()[0]
            or 0
        )
        votes_7d = db.execute("SELECT COUNT(*) FROM community_votes").fetchone()[0] or 0
        reports_open = (
            db.execute("SELECT COUNT(*) FROM community_reports WHERE status = 'open'").fetchone()[0]
            or 0
        )
        complaints_7d = (
            db.execute(
                "SELECT COUNT(*) FROM user_feedback WHERE type = 'complaint' AND created_at >= datetime('now', '-7 days')"
            ).fetchone()[0]
            or 0
        )
        active_users_7d = (
            db.execute(
                "SELECT COUNT(DISTINCT user_email) FROM user_activity WHERE created_at >= datetime('now', '-7 days') AND user_email IS NOT NULL"
            ).fetchone()[0]
            or 0
        )
        avg_rating_row = db.execute(
            "SELECT AVG(rating) FROM satisfaction_surveys WHERE created_at >= datetime('now', '-30 days')"
        ).fetchone()
        avg_rating = (
            float(avg_rating_row[0]) if avg_rating_row and avg_rating_row[0] is not None else None
        )
        return jsonify(
            {
                "success": True,
                "posts_7d": posts_7d,
                "replies_7d": replies_7d,
                "votes_total": votes_7d,
                "open_reports": reports_open,
                "complaints_7d": complaints_7d,
                "active_users_7d": active_users_7d,
                "avg_helpfulness_30d": round(avg_rating, 2) if avg_rating is not None else None,
            }
        )
    except Exception as e:
        logger.exception("Community health error: %s", e)
        return api_error("Could not load community health right now.", 500)


@app.route("/api/openclaw/policy", methods=["GET"])
def openclaw_policy():
    """Publish OpenClaw safety boundaries and legal warnings for the UI."""
    return jsonify(
        {
            "enabled": OPENCLAW_ENABLED,
            "checkout_available": bool(stripe_openclaw_price_id),
            "sandbox_root": OPENCLAW_SANDBOX_ROOT,
            "max_files": OPENCLAW_MAX_FILES,
            "max_bytes": OPENCLAW_MAX_BYTES,
            "rules": [
                "OpenClaw only operates inside a dedicated workspace folder.",
                "No direct system-level access: BIOS/UEFI, boot config, registry, kernel/driver paths are forbidden.",
                "No automatic writes to system folders, user home, or unrelated drives.",
                "High-risk operations require explicit in-app confirmation and preflight checks.",
                "Immutable allowlist guard-check validates operation, path, extension, path depth, and size before execution.",
                "Users are responsible for backups and independent review before applying changes.",
            ],
            "warnings": [
                "Experimental capability. Misuse can break saves, mod setups, or local files.",
                "OpenClaw is not permitted to modify firmware, BIOS/UEFI settings, boot records, registry hives, or kernel drivers.",
                "Do not buy this tier without reviewing the public implementation and safeguards.",
                "Treat this as a power tool: verify outputs manually before running commands.",
            ],
            "hard_limits": {
                "allowed_operations": sorted(OPENCLAW_ALLOWED_OPERATIONS),
                "allowed_extensions": sorted(OPENCLAW_ALLOWED_EXTENSIONS),
                "deny_segments": sorted(OPENCLAW_DENY_SEGMENTS),
                "max_files": OPENCLAW_MAX_FILES,
                "max_bytes": OPENCLAW_MAX_BYTES,
                "max_path_depth": OPENCLAW_MAX_PATH_DEPTH,
                "max_path_length": OPENCLAW_MAX_PATH_LENGTH,
                "require_same_ip_for_grant": OPENCLAW_REQUIRE_SAME_IP,
            },
            "github_url": "https://github.com/SamsonProject/SkyModderAI",
            "guard_check_endpoint": "/api/openclaw/guard-check",
            "grant_verify_endpoint": "/api/openclaw/verify-grant",
            "safety_status_endpoint": "/api/openclaw/safety-status",
            "capabilities_endpoint": "/api/openclaw/capabilities",
            "permissions_endpoint": "/api/openclaw/permissions",
            "plan_propose_endpoint": "/api/openclaw/plan/propose",
            "plan_execute_endpoint": "/api/openclaw/plan/execute",
            "feedback_loop_endpoint": "/api/openclaw/loop/feedback",
            "install_manifest_endpoint": "/api/openclaw/install-manifest",
        }
    )


@app.route("/api/openclaw/request-access", methods=["POST"])
@rate_limit(RATE_LIMIT_API, "openclaw")
@login_required_api
def openclaw_request_access():
    """Collect explicit acknowledgements before enabling OpenClaw workflows."""
    user_email = session.get("user_email")
    tier = get_user_tier(user_email) if user_email else "free"
    if not OPENCLAW_ENABLED:
        return api_error("OpenClaw is currently disabled on this deployment.", 403)

    data = request.get_json() or {}
    acknowledgements = data.get("acknowledgements") or {}
    required_keys = ("read_repo_code", "confirmed_backups", "accepts_experimental_risk")
    missing = [k for k in required_keys if not acknowledgements.get(k)]
    if missing:
        return api_error(
            "All safety acknowledgements are required before access can be granted.",
            400,
            missing=missing,
        )

    workspace_rel = (data.get("workspace_rel") or "openclaw_user_workspace").strip()
    if ".." in workspace_rel or workspace_rel.startswith("/"):
        return api_error("workspace_rel must be a safe relative path.", 400)
    user_ns = hashlib.sha256((user_email or "unknown").encode("utf-8")).hexdigest()[:12]
    effective_workspace = os.path.join(OPENCLAW_SANDBOX_ROOT, user_ns, workspace_rel)

    logger.info(
        "OpenClaw access granted for %s with workspace %s",
        _redact_email(user_email),
        effective_workspace,
    )
    _openclaw_log_event(
        user_email=user_email,
        event_type="grant_issued",
        rel_path=workspace_rel,
        allowed=True,
        reasons=[],
    )
    grant_token = _issue_openclaw_grant(user_email=user_email, workspace_rel=workspace_rel)
    return jsonify(
        {
            "success": True,
            "tier": tier,
            "workspace_rel": workspace_rel,
            "effective_workspace": effective_workspace,
            "grant_token": grant_token,
            "grant_expires_in_seconds": 1800,
            "sandbox_root": OPENCLAW_SANDBOX_ROOT,
            "limits": {"max_files": OPENCLAW_MAX_FILES, "max_bytes": OPENCLAW_MAX_BYTES},
            "message": "Access acknowledged. OpenClaw remains confined to your dedicated workspace and explicit consent flow.",
        }
    )


@app.route("/api/openclaw/verify-grant", methods=["POST"])
@rate_limit(RATE_LIMIT_API, "openclaw")
@login_required_api
def openclaw_verify_grant():
    """Verify active OpenClaw grant token before sensitive workflows."""
    user_email = session.get("user_email")
    data = request.get_json() or {}
    ok, reason = _validate_openclaw_grant(data.get("grant_token") or "", user_email or "")
    if not ok:
        _openclaw_log_event(
            user_email=user_email,
            event_type="grant_verify_failed",
            allowed=False,
            reasons=[reason],
        )
        return api_error(reason, 403)
    _openclaw_log_event(
        user_email=user_email, event_type="grant_verified", allowed=True, reasons=[]
    )
    return jsonify({"success": True, "message": "OpenClaw grant verified."})


def _openclaw_guard_validate(operation: str, rel_path: str, bytes_requested: int = 0):
    """Immutable guard policy for OpenClaw file operations."""
    op = (operation or "").strip().lower()
    if op not in OPENCLAW_ALLOWED_OPERATIONS:
        return False, ["Unsupported operation"]
    clean = (rel_path or "").strip().replace("\\", "/")
    reasons = []
    if not clean or clean.startswith("/") or clean.startswith("~") or ".." in clean:
        reasons.append("Path must be a safe relative path")
    if len(clean) > OPENCLAW_MAX_PATH_LENGTH:
        reasons.append(f"Path exceeds length limit ({OPENCLAW_MAX_PATH_LENGTH})")
    if len(clean.split("/")) > OPENCLAW_MAX_PATH_DEPTH:
        reasons.append(f"Path exceeds depth limit ({OPENCLAW_MAX_PATH_DEPTH})")
    # Extra hard block for Windows drive letters and shell-like injection tokens.
    if ":" in clean or clean.startswith(".\\") or clean.startswith("./../"):
        reasons.append("Path contains forbidden absolute or traversal-like markers")
    if any(tok in clean for tok in ("`", "$(", ";", "&&", "|")):
        reasons.append("Path contains forbidden shell-like tokens")
    for seg in clean.split("/"):
        seg_norm = (seg or "").strip().lower()
        if seg_norm in OPENCLAW_DENY_SEGMENTS:
            reasons.append(f"Path segment not allowed: {seg}")
    ext = os.path.splitext(clean)[1].lower()
    if op in ("write", "delete", "move", "copy") and ext and ext not in OPENCLAW_ALLOWED_EXTENSIONS:
        reasons.append(f"Extension not allowed: {ext}")
    if op in ("write", "copy", "move") and not ext:
        reasons.append("Write/copy/move requires explicit file extension")
    if bytes_requested < 0 or bytes_requested > OPENCLAW_MAX_BYTES:
        reasons.append(f"bytes_requested exceeds limit ({OPENCLAW_MAX_BYTES})")
    return len(reasons) == 0, reasons


def _openclaw_ip_hash() -> str:
    """Hash client IP for minimal audit correlation without storing raw IP."""
    return _request_ip_hash()


def _openclaw_log_event(
    user_email: str,
    event_type: str,
    operation: str = None,
    rel_path: str = None,
    allowed: bool = False,
    reasons=None,
):
    """Persist OpenClaw audit events for forensics and safety tuning."""
    try:
        db = get_db()
        db.execute(
            """
            INSERT INTO openclaw_events (user_email, event_type, operation, rel_path, allowed, reasons_json, ip_hash)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                (user_email or "").lower() or None,
                (event_type or "unknown")[:64],
                (operation or "")[:32] or None,
                (rel_path or "")[:300] or None,
                1 if allowed else 0,
                json.dumps(reasons or [], ensure_ascii=True)[:2000],
                _openclaw_ip_hash(),
            ),
        )
        db.commit()
    except Exception as e:
        logger.debug("openclaw event log failed: %s", e)


def _issue_openclaw_grant(user_email: str, workspace_rel: str, ttl_seconds: int = 1800) -> str:
    """Issue signed short-lived OpenClaw grant token and persist hash."""
    now = int(_time())
    expires_at = now + ttl_seconds
    serializer = URLSafeTimedSerializer(app.config["SECRET_KEY"], salt="openclaw-grant")
    token = serializer.dumps(
        {
            "email": user_email.lower(),
            "workspace_rel": workspace_rel,
            "exp": expires_at,
            "rnd": secrets.token_hex(8),
        }
    )
    token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
    db = get_db()
    db.execute(
        """
        INSERT INTO openclaw_grants (user_email, token_hash, workspace_rel, ip_hash, expires_at)
        VALUES (?, ?, ?, ?, ?)
        """,
        (user_email.lower(), token_hash, workspace_rel, _openclaw_ip_hash(), expires_at),
    )
    db.commit()
    return token


def _validate_openclaw_grant(token: str, user_email: str) -> tuple[bool, str]:
    """Validate signed token and persisted grant record."""
    if not token:
        return False, "Missing grant token."
    serializer = URLSafeTimedSerializer(app.config["SECRET_KEY"], salt="openclaw-grant")
    try:
        payload = serializer.loads(token, max_age=3600)
    except Exception:
        return False, "Invalid or expired grant token."
    if (payload.get("email") or "").lower() != (user_email or "").lower():
        return False, "Grant token user mismatch."
    token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
    row = (
        get_db()
        .execute(
            "SELECT expires_at, ip_hash FROM openclaw_grants WHERE user_email = ? AND token_hash = ?",
            (user_email.lower(), token_hash),
        )
        .fetchone()
    )
    if not row:
        return False, "Grant token not recognized."
    if int(row["expires_at"] or 0) < int(_time()):
        return False, "Grant token expired."
    if (
        OPENCLAW_REQUIRE_SAME_IP
        and (row["ip_hash"] or "")
        and (row["ip_hash"] != _openclaw_ip_hash())
    ):
        return False, "Grant token IP mismatch."
    return True, ""


def _openclaw_decode_grant(token: str):
    """Decode grant token payload for workspace context."""
    serializer = URLSafeTimedSerializer(app.config["SECRET_KEY"], salt="openclaw-grant")
    try:
        return serializer.loads(token, max_age=3600)
    except Exception:
        return None


def _openclaw_require_lab_access(data):
    """Shared OpenClaw authz gate (tier + feature flag + grant token)."""
    user_email = session.get("user_email")
    if not OPENCLAW_ENABLED:
        return None, None, api_error("OpenClaw is currently disabled on this deployment.", 403)
    token = (data or {}).get("grant_token") or ""
    ok, reason = _validate_openclaw_grant(token, user_email or "")
    if not ok:
        _openclaw_log_event(
            user_email=user_email,
            event_type="grant_required_failed",
            allowed=False,
            reasons=[reason],
        )
        return None, None, api_error(reason, 403)
    payload = _openclaw_decode_grant(token) or {}
    workspace_rel = (payload.get("workspace_rel") or "openclaw_user_workspace").strip()
    return user_email, workspace_rel, None


def _openclaw_get_permissions(user_email: str) -> dict:
    """Load scope -> granted map for OpenClaw permissioned capabilities."""
    rows = (
        get_db()
        .execute(
            "SELECT scope, granted FROM openclaw_permissions WHERE user_email = ?",
            ((user_email or "").lower(),),
        )
        .fetchall()
    )
    granted = {r["scope"]: bool(r["granted"]) for r in rows}
    return {scope: bool(granted.get(scope, False)) for scope in OPENCLAW_PERMISSION_SCOPES}


def _openclaw_set_permissions(user_email: str, scopes: list):
    """Upsert granted scopes for a user (all others unchanged)."""
    db = get_db()
    for scope in scopes:
        if scope not in OPENCLAW_PERMISSION_SCOPES:
            continue
        db.execute(
            """
            INSERT INTO openclaw_permissions (user_email, scope, granted, granted_at)
            VALUES (?, ?, 1, CURRENT_TIMESTAMP)
            ON CONFLICT(user_email, scope) DO UPDATE SET granted = 1, granted_at = CURRENT_TIMESTAMP
            """,
            ((user_email or "").lower(), scope),
        )
    db.commit()


def _openclaw_workspace_abs(user_email: str, workspace_rel: str) -> str:
    """Compute user workspace path inside sandbox root."""
    user_ns = hashlib.sha256((user_email or "unknown").encode("utf-8")).hexdigest()[:12]
    return os.path.abspath(os.path.join(OPENCLAW_SANDBOX_ROOT, user_ns, workspace_rel))


def _openclaw_write_state_json(user_email: str, workspace_rel: str, rel_path: str, payload: dict):
    """Write JSON payload inside sandbox workspace with guard validation."""
    body = json.dumps(payload or {}, ensure_ascii=True, indent=2)
    body_bytes = len(body.encode("utf-8"))
    allowed, reasons = _openclaw_guard_validate("write", rel_path, body_bytes)
    if not allowed:
        return False, reasons
    ws = _openclaw_workspace_abs(user_email, workspace_rel)
    target = os.path.abspath(os.path.join(ws, rel_path))
    if not target.startswith(ws):
        return False, ["Resolved path escapes workspace"]
    os.makedirs(os.path.dirname(target), exist_ok=True)
    with open(target, "w", encoding="utf-8") as f:
        f.write(body)
    return True, []


@app.route("/api/openclaw/guard-check", methods=["POST"])
@rate_limit(RATE_LIMIT_API, "openclaw")
@login_required_api
def openclaw_guard_check():
    """Dry-run policy checker for OpenClaw operations (no side effects)."""
    user_email = session.get("user_email")
    if not OPENCLAW_ENABLED:
        return api_error("OpenClaw is currently disabled on this deployment.", 403)
    data = request.get_json() or {}
    ok, reason = _validate_openclaw_grant(data.get("grant_token") or "", user_email or "")
    if not ok:
        return api_error(reason, 403)
    operation = data.get("operation") or "read"
    rel_path = data.get("rel_path") or ""
    try:
        bytes_requested = int(data.get("bytes_requested") or 0)
    except (TypeError, ValueError):
        bytes_requested = 0
    try:
        files_touched = int(data.get("files_touched") or 0)
    except (TypeError, ValueError):
        files_touched = 0
    if files_touched < 0:
        files_touched = 0
    allowed, reasons = _openclaw_guard_validate(operation, rel_path, bytes_requested)
    if files_touched > OPENCLAW_MAX_FILES:
        allowed = False
        reasons = list(reasons) + [f"files_touched exceeds limit ({OPENCLAW_MAX_FILES})"]
    _openclaw_log_event(
        user_email=user_email,
        event_type="guard_check",
        operation=operation,
        rel_path=rel_path,
        allowed=allowed,
        reasons=reasons,
    )
    return jsonify(
        {
            "success": True,
            "allowed": allowed,
            "dry_run_only": True,
            "operation": operation,
            "rel_path": rel_path,
            "bytes_requested": bytes_requested,
            "reasons": reasons,
            "policy": {
                "allowed_operations": sorted(OPENCLAW_ALLOWED_OPERATIONS),
                "allowed_extensions": sorted(OPENCLAW_ALLOWED_EXTENSIONS),
                "deny_segments": sorted(OPENCLAW_DENY_SEGMENTS),
                "max_files": OPENCLAW_MAX_FILES,
                "max_bytes": OPENCLAW_MAX_BYTES,
                "max_path_depth": OPENCLAW_MAX_PATH_DEPTH,
                "max_path_length": OPENCLAW_MAX_PATH_LENGTH,
                "sandbox_root": OPENCLAW_SANDBOX_ROOT,
            },
        }
    )


@app.route("/api/openclaw/permissions", methods=["GET", "POST"])
@rate_limit(RATE_LIMIT_API, "openclaw")
@login_required_api
def openclaw_permissions():
    """Get or grant scoped OpenClaw permissions."""
    if request.method == "GET":
        data = request.args.to_dict()
    else:
        data = request.get_json() or {}
    user_email, workspace_rel, err = _openclaw_require_lab_access(data)
    if err:
        return err

    if request.method == "GET":
        granted = _openclaw_get_permissions(user_email)
        return jsonify(
            {
                "success": True,
                "workspace_rel": workspace_rel,
                "available_scopes": OPENCLAW_PERMISSION_SCOPES,
                "granted": granted,
            }
        )

    scopes = data.get("scopes") or []
    if not isinstance(scopes, list):
        return api_error("scopes must be an array.", 400)
    clean_scopes = [str(s).strip() for s in scopes if str(s).strip() in OPENCLAW_PERMISSION_SCOPES]
    if not clean_scopes:
        return api_error(
            "No valid permission scopes requested.",
            400,
            available_scopes=OPENCLAW_PERMISSION_SCOPES,
        )
    _openclaw_set_permissions(user_email, clean_scopes)
    _openclaw_log_event(
        user_email=user_email,
        event_type="permissions_granted",
        allowed=True,
        reasons=clean_scopes,
    )
    return jsonify(
        {
            "success": True,
            "workspace_rel": workspace_rel,
            "granted_scopes": _openclaw_get_permissions(user_email),
        }
    )


@app.route("/api/openclaw/plan/propose", methods=["POST"])
@rate_limit(RATE_LIMIT_API, "openclaw")
@login_required_api
def openclaw_plan_propose():
    """Build a scoped OpenClaw improvement loop plan (proposal only)."""
    data = request.get_json() or {}
    user_email, workspace_rel, err = _openclaw_require_lab_access(data)
    if err:
        return err
    granted = _openclaw_get_permissions(user_email)
    game = (data.get("game") or DEFAULT_GAME).lower()
    if game not in {g["id"] for g in SUPPORTED_GAMES}:
        game = DEFAULT_GAME

    plan_body = build_openclaw_plan(
        game=game,
        objective=(
            data.get("objective") or "improve stability and visuals while keeping safety strict"
        ),
        playstyle=(data.get("playstyle") or "balanced"),
        permissions=granted,
        telemetry=(data.get("telemetry") or {}),
    )

    actions = plan_body.get("actions", [])
    preflight = []
    for idx, a in enumerate(actions):
        fa = a.get("file_action") or {}
        if not fa:
            continue
        allowed, reasons = _openclaw_guard_validate(
            fa.get("operation") or "write",
            fa.get("rel_path") or "",
            int(fa.get("bytes_requested") or 0),
        )
        preflight.append(
            {"action_index": idx, "allowed": allowed, "reasons": reasons, "file_action": fa}
        )

    plan_id = secrets.token_hex(8)
    plan_payload = {
        "plan_id": plan_id,
        "workspace_rel": workspace_rel,
        "permissions": granted,
        "preflight": preflight,
        **plan_body,
    }
    get_db().execute(
        """
        INSERT INTO openclaw_plan_runs (user_email, plan_id, game, objective, status, plan_json)
        VALUES (?, ?, ?, ?, 'proposed', ?)
        """,
        (
            (user_email or "").lower(),
            plan_id,
            game,
            (plan_body.get("objective") or "")[:300],
            json.dumps(plan_payload, ensure_ascii=True)[:200000],
        ),
    )
    get_db().commit()
    _openclaw_log_event(
        user_email=user_email,
        event_type="plan_proposed",
        rel_path=".openclaw/plans",
        allowed=True,
        reasons=[plan_id],
    )
    return jsonify({"success": True, "plan": plan_payload, "requires_approval": True})


@app.route("/api/openclaw/plan/execute", methods=["POST"])
@rate_limit(RATE_LIMIT_API, "openclaw")
@login_required_api
def openclaw_plan_execute():
    """Execute approved OpenClaw plan actions within sandbox constraints."""
    data = request.get_json() or {}
    user_email, workspace_rel, err = _openclaw_require_lab_access(data)
    if err:
        return err
    if not data.get("confirmed"):
        return api_error("Execution requires explicit confirmation.", 400)

    plan_id = (data.get("plan_id") or "").strip()
    if not plan_id:
        return api_error("plan_id required.", 400)
    row = (
        get_db()
        .execute(
            "SELECT plan_json, status FROM openclaw_plan_runs WHERE user_email = ? AND plan_id = ?",
            ((user_email or "").lower(), plan_id),
        )
        .fetchone()
    )
    if not row:
        return api_error("Plan not found.", 404)
    plan_payload = json.loads(row["plan_json"] or "{}")
    if row["status"] == "executed":
        return api_error("Plan already executed.", 409)

    executed_actions = []
    blocked_actions = []
    for idx, a in enumerate(plan_payload.get("actions", [])):
        fa = (a or {}).get("file_action") or {}
        if fa:
            ok, reasons = _openclaw_guard_validate(
                fa.get("operation") or "write",
                fa.get("rel_path") or "",
                int(fa.get("bytes_requested") or 0),
            )
            if not ok:
                blocked_actions.append({"action_index": idx, "reason": reasons})
                continue
            payload = {"plan_id": plan_id, "action": a}
            wrote, write_reasons = _openclaw_write_state_json(
                user_email=user_email,
                workspace_rel=workspace_rel,
                rel_path=(fa.get("rel_path") or ".openclaw/state/action.json"),
                payload=payload,
            )
            if not wrote:
                blocked_actions.append({"action_index": idx, "reason": write_reasons})
                continue
        executed_actions.append({"action_index": idx, "kind": a.get("kind") or "unknown"})

    get_db().execute(
        "UPDATE openclaw_plan_runs SET status = 'executed', executed_at = CURRENT_TIMESTAMP WHERE user_email = ? AND plan_id = ?",
        ((user_email or "").lower(), plan_id),
    )
    get_db().commit()
    _openclaw_log_event(
        user_email=user_email,
        event_type="plan_executed",
        rel_path=".openclaw/plans",
        allowed=True,
        reasons=[f"executed={len(executed_actions)}", f"blocked={len(blocked_actions)}"],
    )
    return jsonify(
        {
            "success": True,
            "plan_id": plan_id,
            "executed_actions": executed_actions,
            "blocked_actions": blocked_actions,
            "next_step": "Submit runtime feedback to /api/openclaw/loop/feedback for the next refinement cycle.",
        }
    )


@app.route("/api/openclaw/loop/feedback", methods=["POST"])
@rate_limit(RATE_LIMIT_API, "openclaw")
@login_required_api
def openclaw_loop_feedback():
    """Record post-run feedback and return next-loop adjustment suggestions."""
    data = request.get_json() or {}
    user_email, workspace_rel, err = _openclaw_require_lab_access(data)
    if err:
        return err
    game = (data.get("game") or DEFAULT_GAME).lower()
    if game not in {g["id"] for g in SUPPORTED_GAMES}:
        game = DEFAULT_GAME

    feedback = {
        "fps_avg": data.get("fps_avg"),
        "crashes": data.get("crashes") or 0,
        "stutter_events": data.get("stutter_events") or 0,
        "enjoyment_score": data.get("enjoyment_score"),
        "notes": (data.get("notes") or "")[:2000],
    }
    suggestions = suggest_loop_adjustments(feedback)
    get_db().execute(
        """
        INSERT INTO openclaw_feedback (user_email, game, fps_avg, crashes, stutter_events, enjoyment_score, notes, feedback_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            (user_email or "").lower(),
            game,
            feedback.get("fps_avg"),
            int(feedback.get("crashes") or 0),
            int(feedback.get("stutter_events") or 0),
            feedback.get("enjoyment_score"),
            feedback.get("notes"),
            json.dumps(feedback, ensure_ascii=True),
        ),
    )
    get_db().commit()
    _openclaw_write_state_json(
        user_email=user_email,
        workspace_rel=workspace_rel,
        rel_path=".openclaw/loop/latest_feedback.json",
        payload={
            "feedback": feedback,
            "suggestions": suggestions,
            "updated_at": datetime.utcnow().isoformat() + "Z",
        },
    )
    _openclaw_log_event(
        user_email=user_email,
        event_type="loop_feedback",
        rel_path=".openclaw/loop",
        allowed=True,
        reasons=suggestions[:2],
    )
    return jsonify(
        {
            "success": True,
            "game": game,
            "feedback": feedback,
            "suggestions": suggestions,
            "loop_state_written": True,
        }
    )


def _openclaw_safety_status():
    """Compute OpenClaw hardening status as a simple score/checklist."""
    checks = [
        ("feature_toggle", OPENCLAW_ENABLED, "Feature toggle present and explicit"),
        ("workspace_root_set", bool(OPENCLAW_SANDBOX_ROOT), "Dedicated sandbox root configured"),
        ("same_ip_grants", OPENCLAW_REQUIRE_SAME_IP, "Grant token bound to same IP hash"),
        ("max_files_guard", OPENCLAW_MAX_FILES <= 1000, "File-touch guard within conservative cap"),
        (
            "max_bytes_guard",
            OPENCLAW_MAX_BYTES <= 100 * 1024 * 1024,
            "Byte guard within conservative cap",
        ),
        (
            "op_allowlist",
            len(OPENCLAW_ALLOWED_OPERATIONS) <= 12,
            "Operation allowlist is constrained",
        ),
        (
            "denylist_has_system_markers",
            any(x in OPENCLAW_DENY_SEGMENTS for x in ("system32", "bios", "efi", "registry")),
            "System-critical path denylist present",
        ),
    ]
    passed = sum(1 for _, ok, _ in checks if ok)
    score = int(round((passed / len(checks)) * 100))
    return {
        "score": score,
        "checks": [{"id": cid, "ok": ok, "description": desc} for cid, ok, desc in checks],
        "status": "strict" if score >= 85 else ("moderate" if score >= 60 else "weak"),
    }


@app.route("/api/openclaw/safety-status", methods=["GET"])
def openclaw_safety_status():
    """Return OpenClaw hardening posture and immutable constraints."""
    status = _openclaw_safety_status()
    return jsonify(
        {
            "success": True,
            "enabled": OPENCLAW_ENABLED,
            "hardening": status,
            "policy": {
                "sandbox_root": OPENCLAW_SANDBOX_ROOT,
                "allowed_operations": sorted(OPENCLAW_ALLOWED_OPERATIONS),
                "allowed_extensions": sorted(OPENCLAW_ALLOWED_EXTENSIONS),
                "deny_segments": sorted(OPENCLAW_DENY_SEGMENTS),
                "max_files": OPENCLAW_MAX_FILES,
                "max_bytes": OPENCLAW_MAX_BYTES,
                "max_path_depth": OPENCLAW_MAX_PATH_DEPTH,
                "max_path_length": OPENCLAW_MAX_PATH_LENGTH,
                "require_same_ip_for_grant": OPENCLAW_REQUIRE_SAME_IP,
            },
        }
    )


@app.route("/api/openclaw/capabilities", methods=["GET"])
def openclaw_capabilities():
    """
    Publish safe capability map for OpenClaw UX planning.
    This is intentionally explicit about what is out-of-scope (BIOS/firmware/kernel).
    """
    return jsonify(
        {
            "success": True,
            "enabled": OPENCLAW_ENABLED,
            "capabilities": {
                "safe_now": [
                    "LOOT-aware analysis and recommendation loops",
                    "Sandboxed file planning with guard-check",
                    "Permission-scoped plan propose -> approve -> execute workflow",
                    "Non-destructive telemetry and feedback loops",
                    "Browser-side controller detection (user-consented, read-only signal)",
                    "Browser-side input pattern signals (user-consented, aggregated)",
                ],
                "conditionally_safe": [
                    "Benchmark-and-compare loops with explicit user opt-in",
                    "Preset suggestions that require manual user apply",
                    "Internet-assisted research for compatibility/perf heuristics",
                ],
                "blocked_hard": [
                    "BIOS/UEFI writes",
                    "Bootloader or firmware changes",
                    "Registry hive writes",
                    "Kernel driver installs or modification",
                    "Silent system-level process injection",
                ],
            },
            "notes": [
                "OpenClaw is designed for constrained experimentation, not privileged machine control.",
                "Any higher-risk capability should remain opt-in, preview-first, and guard-checked.",
            ],
        }
    )


@app.route("/api/openclaw/install-manifest", methods=["GET"])
def openclaw_install_manifest():
    """Return companion install/permission manifest for local OpenClaw runtime."""
    return jsonify(
        {
            "success": True,
            "enabled": OPENCLAW_ENABLED,
            "companion": {
                "name": "OpenClaw Companion (planned local runtime)",
                "model": "local helper process + permission prompts + sandbox workspace",
                "install_targets": ["windows", "linux", "macos"],
                "required_permissions": [
                    {
                        "scope": "launch_game",
                        "prompt": "Allow OpenClaw to launch the game through a wrapper intent?",
                    },
                    {
                        "scope": "read_game_logs",
                        "prompt": "Allow read-only parsing of runtime/game logs?",
                    },
                    {
                        "scope": "read_performance_metrics",
                        "prompt": "Allow collection of FPS/frametime summaries?",
                    },
                    {
                        "scope": "controller_signal",
                        "prompt": "Allow aggregated controller usage signal?",
                    },
                    {
                        "scope": "input_signal_aggregate",
                        "prompt": "Allow aggregated input pattern signal (no raw key logging)?",
                    },
                    {
                        "scope": "internet_research",
                        "prompt": "Allow trusted web lookup for compatibility/performance ideas?",
                    },
                    {
                        "scope": "write_sandbox_files",
                        "prompt": "Allow writing plans/checkpoints only inside OpenClaw sandbox workspace?",
                    },
                ],
                "blocked_hard": [
                    "firmware/BIOS/UEFI changes",
                    "bootloader modification",
                    "registry hive writes",
                    "kernel/driver install hooks",
                    "silent privileged system changes",
                ],
            },
            "bootstrap": {
                "workspace": OPENCLAW_SANDBOX_ROOT,
                "recommendation": "Use /api/openclaw/request-access then /api/openclaw/permissions before any plan execution.",
            },
        }
    )


@app.route("/api/profile/links", methods=["GET"])
@login_required_api
def api_profile_links_get():
    """Get linked profile/account handles for current user."""
    user_email = session.get("user_email")
    return jsonify({"links": get_user_links(user_email)})


@app.route("/api/profile/links", methods=["POST"])
@login_required_api
def api_profile_links_save():
    """Save linked profile/account handles for current user."""
    data = request.get_json() or {}
    user_email = session.get("user_email")
    links = {
        "nexus_profile_url": (data.get("nexus_profile_url") or "").strip(),
        "github_username": (data.get("github_username") or "").strip(),
        "discord_handle": (data.get("discord_handle") or "").strip(),
    }
    if links["nexus_profile_url"] and not links["nexus_profile_url"].startswith(
        ("https://www.nexusmods.com/", "https://next.nexusmods.com/")
    ):
        return api_error("Nexus profile URL must be a valid Nexus Mods profile link.", 400)
    set_user_links(user_email, links)
    return jsonify({"success": True, "links": get_user_links(user_email)})


@app.route("/api/profile/dashboard", methods=["GET"])
@login_required_api
def api_profile_dashboard():
    """Return dynamic profile dashboard data for community and product engagement."""
    user_email = (session.get("user_email") or "").lower()
    if not user_email:
        return api_error("Not signed in.", 401)
    try:
        db = get_db()
        posts_count = (
            db.execute(
                "SELECT COUNT(*) FROM community_posts WHERE user_email = ?",
                (user_email,),
            ).fetchone()[0]
            or 0
        )
        replies_count = (
            db.execute(
                "SELECT COUNT(*) FROM community_replies WHERE user_email = ?",
                (user_email,),
            ).fetchone()[0]
            or 0
        )
        votes_cast = (
            db.execute(
                "SELECT COUNT(*) FROM community_votes WHERE user_email = ?",
                (user_email,),
            ).fetchone()[0]
            or 0
        )
        feedback_count = (
            db.execute(
                "SELECT COUNT(*) FROM user_feedback WHERE user_email = ?",
                (user_email,),
            ).fetchone()[0]
            or 0
        )
        avg_helpfulness_row = db.execute(
            "SELECT AVG(rating) FROM satisfaction_surveys WHERE user_email = ?",
            (user_email,),
        ).fetchone()
        avg_helpfulness = avg_helpfulness_row[0] if avg_helpfulness_row else None

        top_tags_rows = db.execute(
            """
            SELECT tag, COUNT(*) AS c
            FROM community_posts
            WHERE user_email = ? AND tag IS NOT NULL AND tag != ''
            GROUP BY tag
            ORDER BY c DESC, tag ASC
            LIMIT 5
            """,
            (user_email,),
        ).fetchall()
        top_tags = [{"tag": r["tag"], "count": int(r["c"] or 0)} for r in top_tags_rows]

        activity_rows = db.execute(
            """
            SELECT event_type, event_data, created_at
            FROM user_activity
            WHERE user_email = ?
            ORDER BY created_at DESC
            LIMIT 20
            """,
            (user_email,),
        ).fetchall()
        recent_activity = []
        for r in activity_rows:
            event_data = {}
            try:
                if r["event_data"]:
                    event_data = json.loads(r["event_data"])
            except Exception:
                event_data = {}
            recent_activity.append(
                {
                    "event_type": r["event_type"],
                    "event_data": event_data,
                    "created_at": r["created_at"],
                }
            )

        # Friendly suggested next actions based on participation and outcomes.
        suggestions = []
        if posts_count == 0:
            suggestions.append(
                "Introduce yourself in Community with your game + mod manager + plugin count."
            )
        if replies_count < 2:
            suggestions.append(
                "Reply to a help thread to build trust and discover edge-case fixes."
            )
        if feedback_count == 0:
            suggestions.append(
                "Use the feedback button after your next run so Samson can tune suggestions better."
            )
        if avg_helpfulness is None or (avg_helpfulness and avg_helpfulness < 3.5):
            suggestions.append(
                "Run Analyze after Build a List and follow red errors first, then warnings."
            )
        if not top_tags:
            suggestions.append(
                "Pick a community tag (tip/help/dev) on your next post so others can find you faster."
            )
        suggestions = suggestions[:4]

        track_activity(
            "profile_dashboard_view", {"posts": posts_count, "replies": replies_count}, user_email
        )
        return jsonify(
            {
                "success": True,
                "stats": {
                    "posts_count": posts_count,
                    "replies_count": replies_count,
                    "votes_cast": votes_cast,
                    "feedback_count": feedback_count,
                    "avg_helpfulness": round(float(avg_helpfulness), 2)
                    if avg_helpfulness is not None
                    else None,
                },
                "top_tags": top_tags,
                "recent_activity": recent_activity,
                "suggestions": suggestions,
            }
        )
    except Exception as e:
        logger.exception("Profile dashboard error: %s", e)
        return api_error("Could not load profile dashboard right now.", 500)


@app.route("/api/specs", methods=["GET"])
def api_specs_get():
    """Get current user's system specs (or empty)."""
    user_email = session.get("user_email")
    specs = get_user_specs(user_email) if user_email else None
    return jsonify({"specs": specs or {}})


@app.route("/api/specs", methods=["POST"])
def api_specs_save():
    """Save system specs. Body: {cpu, gpu, ram_gb, vram_gb, resolution, storage_type} or {steam_paste: "..."}.
    Logged-in: saves to DB. Guest: returns parsed specs (use localStorage on client)."""
    data = request.get_json() or {}
    user_email = session.get("user_email")
    steam = (data.get("steam_paste") or "").strip()
    if steam:
        specs = parse_steam_system_info(steam)
    else:
        specs = {
            k: (str(data.get(k) or "").strip() or None)
            for k in ("cpu", "gpu", "ram_gb", "vram_gb", "resolution", "storage_type")
        }
        specs = {k: v for k, v in specs.items() if v is not None}
    if user_email and specs:
        set_user_specs(user_email, specs)
    return jsonify(
        {"success": True, "specs": specs or (get_user_specs(user_email) if user_email else {})}
    )


@app.route("/api/specs/parse-steam", methods=["POST"])
def api_specs_parse_steam():
    """Parse Steam System Info paste. Body: {text: "..."}. Returns parsed specs (no auth required)."""
    data = request.get_json() or {}
    text = (data.get("text") or data.get("steam_paste") or "").strip()
    specs = parse_steam_system_info(text)
    return jsonify({"specs": specs})


@app.route("/logout")
def logout():
    """Revoke current session, clear cookie, redirect to index."""
    token = request.cookies.get(SESSION_COOKIE_NAME)
    if token:
        session_revoke(token)
    session.clear()
    resp = redirect(url_for("index"))
    resp.set_cookie(
        SESSION_COOKIE_NAME,
        "",
        max_age=0,
        httponly=True,
        secure=app.config["SESSION_COOKIE_SECURE"],
        samesite=app.config["SESSION_COOKIE_SAMESITE"],
    )
    return resp


@app.route("/manifest.json")
def manifest_json():
    """PWA manifest with correct MIME type."""
    return (
        app.send_static_file("manifest.json"),
        200,
        {
            "Content-Type": "application/manifest+json",
        },
    )


@app.route("/api/platform-capabilities", methods=["GET"])
def platform_capabilities():
    """Surface runtime capability flags for UI and testing."""
    user_email = session.get("user_email")
    tier = get_user_tier(user_email) if user_email else "free"
    return jsonify(
        {
            "success": True,
            "offline_mode": OFFLINE_MODE,
            "payments_enabled": PAYMENTS_ENABLED,
            "openclaw_enabled": OPENCLAW_ENABLED,
            "openclaw_checkout_available": bool(stripe_openclaw_price_id),
            "ai_chat_enabled": AI_CHAT_ENABLED,
            "tier": tier,
            "tier_label": tier_label(tier),
            "has_paid_access": has_paid_access(tier),
            "agent_feed_url": "/ai-feed.json",
        }
    )


@app.route("/robots.txt")
def robots_txt():
    """SEO: Allow all crawlers + advertise sitemap."""
    base = request.host_url.rstrip("/")
    body = f"User-agent: *\nAllow: /\nSitemap: {base}/sitemap.xml\n"
    return Response(body, mimetype="text/plain")


@app.route("/sitemap.xml")
def sitemap_xml():
    """Basic sitemap for key pages and API discovery hubs."""
    base = request.host_url.rstrip("/")
    urls = [
        "/",
        "/quickstart",
        "/profile",
        "/terms",
        "/privacy",
        "/safety",
        "/api",
        "/ai-feed.json",
    ]
    entries = "".join(
        f"<url><loc>{base}{u}</loc><changefreq>daily</changefreq><priority>{'1.0' if u == '/' else '0.7'}</priority></url>"
        for u in urls
    )
    xml = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
        f"{entries}"
        "</urlset>"
    )
    return Response(xml, mimetype="application/xml")


@app.route("/api/information-map", methods=["GET"])
def information_map():
    """Information flow map: what data enters, where it goes, and what acts on it."""
    return jsonify(
        {
            "success": True,
            "principle": "Information is collected only when useful, processed with explicit purpose, and constrained by safety boundaries.",
            "inputs": {
                "user_inputs": [
                    "mod_list",
                    "build_preferences",
                    "specs",
                    "community_posts",
                    "dev_files",
                    "feedback",
                ],
                "runtime_signals": [
                    "activity_events",
                    "satisfaction_scores",
                    "openclaw_loop_feedback",
                ],
                "external_sources": [
                    "LOOT masterlist",
                    "optional web search fallback",
                    "public GitHub repo content (dev mode)",
                ],
            },
            "processing": {
                "parsing": ["parse_mod_list_text", "modlist_normalize"],
                "ranking": [
                    "BM25 search engine",
                    "recommendation heuristics",
                    "system impact scoring",
                ],
                "ai_layers": [
                    "analysis assistant",
                    "dev assistant",
                    "samson loop suggestions",
                    "openclaw plan engine",
                ],
                "safety_layers": [
                    "rate limits",
                    "tier gates",
                    "openclaw grant token",
                    "immutable guard-check policy",
                ],
            },
            "stores": {
                "users_db_tables": [
                    "users",
                    "user_sessions",
                    "api_keys",
                    "user_specs",
                    "user_links",
                    "community_posts",
                    "community_replies",
                    "community_votes",
                    "community_reports",
                    "user_feedback",
                    "user_activity",
                    "satisfaction_surveys",
                    "openclaw_grants",
                    "openclaw_events",
                    "openclaw_permissions",
                    "openclaw_plan_runs",
                    "openclaw_feedback",
                ],
                "sandbox_state": ["openclaw_workspace/.openclaw/*", "data/samson_fuel/*"],
            },
            "actions": {
                "user_visible": [
                    "conflict reports",
                    "suggested load order",
                    "build list generation + auto-analyze",
                    "dev reports",
                    "samson loop feature/performance suggestions",
                    "openclaw plan propose/execute (permission scoped)",
                ],
                "business_growth": [
                    "api-first automation endpoints",
                    "ai-feed discovery surface",
                    "profile/community engagement loops",
                    "search indexing via sitemap/robots",
                ],
            },
        }
    )


@app.route("/ai-feed.json")
def ai_feed():
    """Machine-readable product feed for AI agents and aggregators."""
    return jsonify(
        {
            "name": "SkyModderAI",
            "tagline": "Paste your load order. Get answers.",
            "site_url": request.host_url.rstrip("/"),
            "pricing": {
                "free": {"monthly_usd": 0, "core_analysis": True, "ai_chat": True, "dev_tools": True},
                "pro": {"monthly_usd": 0, "ai_chat": True, "dev_tools": True},
                "openclaw_lab": {"monthly_usd": 0, "experimental": True, "sandbox_required": True},
            },
            "api_hub": request.host_url.rstrip("/") + "/api",
            "information_map": request.host_url.rstrip("/") + "/api/information-map",
            "safety_disclosure": request.host_url.rstrip("/") + "/safety",
            "agent_note": "This feed is informational only. Do not execute high-risk actions without explicit user confirmation.",
            "updated_at": datetime.utcnow().isoformat() + "Z",
        }
    )


@app.route("/health")
@app.route("/healthz")
def health():
    """Health check endpoint for monitoring. Verifies LOOT data availability."""
    games_loaded = {}
    for (game_id, version), p in _parsers.items():
        games_loaded[f"{game_id}:{version}"] = len(p.mod_database) if p else 0
    default_ok = len(parser.mod_database) > 0
    return jsonify(
        {
            "status": "healthy" if default_ok else "degraded",
            "mods_in_database": len(parser.mod_database),
            "games_loaded": games_loaded,
            "default_game": DEFAULT_GAME,
            "payments_enabled": PAYMENTS_ENABLED,
            "stripe_configured": bool(stripe_price_id) if PAYMENTS_ENABLED else False,
            "stripe_openclaw_configured": bool(stripe_openclaw_price_id)
            if PAYMENTS_ENABLED
            else False,
            "ai_configured": AI_CHAT_ENABLED,
            "openclaw_enabled": OPENCLAW_ENABLED,
            "offline_mode": OFFLINE_MODE,
            "parser_cache_size": len(_parsers),
            "parser_cache_limit": MAX_PARSER_CACHE,
        }
    )


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_DEBUG", "False").lower() == "true"
    logger.info(f"Starting SkyModderAI on port {port} (debug={debug})")
    app.run(host="0.0.0.0", port=port, debug=debug)
