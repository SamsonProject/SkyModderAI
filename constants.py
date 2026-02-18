"""
SkyModderAI Shared Constants
Single source of truth for limits, thresholds, and magic numbers.
Used by app.py, conflict_detector, mod_warnings, system_impact.
"""

from __future__ import annotations

# =============================================================================
# Plugin Limits (Bethesda engine constraints)
# =============================================================================
PLUGIN_LIMIT = 255  # Maximum ESP/ESM plugins (0-254, with 255 reserved)
PLUGIN_LIMIT_WARN_THRESHOLD = 253  # Warn user before hitting limit
ESL_LIMIT = 4096  # Maximum ESL light plugins

# =============================================================================
# Input Size Limits
# =============================================================================
MAX_INPUT_SIZE = 100_000  # 100KB - general input limit
MAX_MOD_LIST_SIZE = 100_000  # 100KB - mod list input limit
MAX_SEARCH_QUERY_LENGTH = 200  # Maximum search query length
MAX_LIST_NAME_LENGTH = 100  # Maximum saved list name length
MAX_EMAIL_LENGTH = 254  # RFC 5321 compliant email length
MAX_USER_AGENT_LENGTH = 512  # Maximum user agent string length

# =============================================================================
# Rate Limits (per window)
# =============================================================================
RATE_LIMIT_WINDOW = 60  # 1 minute window
RATE_LIMIT_ANALYZE = 30  # Max analyze requests per window
RATE_LIMIT_SEARCH = 60  # Max search requests per window
RATE_LIMIT_API = 100  # Max API requests per window
RATE_LIMIT_AUTH = 10  # Max auth requests per window
RATE_LIMIT_DEFAULT = 100  # Default rate limit

# =============================================================================
# Session Configuration
# =============================================================================
SESSION_SHORT_LIFETIME = 86400  # 24 hours
SESSION_LONG_LIFETIME = 30 * 86400  # 30 days (remember me)
SESSION_COOKIE_NAME = "session_token"
STATE_TOKEN_MAX_AGE = 600  # 10 minutes for OAuth state tokens

# =============================================================================
# Security Constants
# =============================================================================
MIN_PASSWORD_LENGTH = 8
MAX_PASSWORD_LENGTH = 128
MIN_SECRET_KEY_LENGTH = 32
API_KEY_PREFIX_LENGTH = 8  # Show first N chars of API keys

# =============================================================================
# Pagination & Display Limits
# =============================================================================
DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 50
DEFAULT_SEARCH_LIMIT = 10
MAX_SEARCH_LIMIT = 50
MAX_CONFLICTS_DISPLAY = 10  # Max conflicts to display before truncation

# =============================================================================
# Cache Configuration
# =============================================================================
CACHE_TTL_DEFAULT = 3600  # 1 hour
CACHE_TTL_LOOT = 86400 * 7  # 7 days for LOOT data
CACHE_TTL_VERSIONS = 86400  # 1 day for version data
MAX_PARSER_CACHE = 8  # Maximum LOOT parsers to cache

# =============================================================================
# File & Path Limits (OpenClaw)
# =============================================================================
OPENCLAW_MAX_FILES = 500
OPENCLAW_MAX_BYTES = 50 * 1024 * 1024  # 50MB
OPENCLAW_MAX_PATH_DEPTH = 10
OPENCLAW_MAX_PATH_LENGTH = 220

# =============================================================================
# AI/LLM Configuration
# =============================================================================
AI_MAX_TOKENS = 2048
AI_TEMPERATURE = 0.7
AI_TIMEOUT_SECONDS = 30

# =============================================================================
# Email Configuration
# =============================================================================
EMAIL_VERIFICATION_TOKEN_MAX_AGE = 86400  # 24 hours
PASSWORD_RESET_TOKEN_MAX_AGE = 3600  # 1 hour
EMAIL_SUBJECT_PREFIX = "[SkyModderAI]"

# =============================================================================
# Error Messages (centralized for consistency)
# =============================================================================
ERROR_INVALID_GAME_ID = "Invalid game ID. Must be one of the supported games."
ERROR_INVALID_MOD_LIST = "Mod list is required and must be valid."
ERROR_MOD_LIST_TOO_LARGE = f"Mod list too large (max {MAX_MOD_LIST_SIZE // 1024}KB)"
ERROR_SEARCH_QUERY_REQUIRED = "Search query is required"
ERROR_SEARCH_QUERY_TOO_LONG = f"Search query too long (max {MAX_SEARCH_QUERY_LENGTH} characters)"
ERROR_EMAIL_REQUIRED = "Email is required"
ERROR_EMAIL_INVALID = "Invalid email format"
ERROR_PASSWORD_TOO_SHORT = f"Password must be at least {MIN_PASSWORD_LENGTH} characters"
ERROR_UNAUTHORIZED = "Authentication required"
ERROR_FORBIDDEN = "You do not have permission to access this resource"
ERROR_NOT_FOUND = "Resource not found"
ERROR_RATE_LIMIT_EXCEEDED = "Rate limit exceeded. Please try again later."
ERROR_INTERNAL_SERVER = "An internal error occurred. Please try again later."

# =============================================================================
# Supported Games (canonical list)
# =============================================================================
SUPPORTED_GAME_IDS = frozenset({
    "skyrimse", "skyrim", "skyrimvr",
    "oblivion",
    "fallout3", "falloutnv", "fallout4",
    "starfield"
})

# =============================================================================
# Tier Names
# =============================================================================
TIER_FREE = "free"
TIER_PRO = "pro"
TIER_PRO_PLUS = "pro_plus"
TIER_CLAW = "claw"
PAID_TIERS = frozenset({TIER_PRO, TIER_PRO_PLUS, TIER_CLAW})
