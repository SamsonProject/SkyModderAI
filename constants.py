"""
SkyModderAI Shared Constants
Single source of truth for limits, thresholds, and magic numbers.
Used by app.py, conflict_detector, mod_warnings, system_impact.
"""

# Bethesda engine plugin limit (non-ESL); ESLs use separate range
PLUGIN_LIMIT = 255
PLUGIN_LIMIT_WARN_THRESHOLD = 253

# Input size limits
MAX_INPUT_SIZE = 100_000  # 100KB

# Rate limits (per window)
RATE_LIMIT_WINDOW = 60
RATE_LIMIT_ANALYZE = 30
RATE_LIMIT_SEARCH = 60
RATE_LIMIT_API = 100
