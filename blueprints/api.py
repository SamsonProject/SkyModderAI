"""
SkyModderAI - API Blueprint

RESTful API endpoints for programmatic access.
Versioned API with proper error handling and documentation.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, Callable

from flask import Blueprint, g, jsonify, request

from exceptions import (
    AnalysisError,
    AuthenticationError,
    InvalidGameIDError,
    InvalidModListError,
    RateLimitError,
    ValidationError,
)
from logging_utils import get_request_id
from security_utils import rate_limit, validate_game_id, validate_mod_list

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)

# Create blueprint with version prefix
api_bp = Blueprint("api", __name__, url_prefix="/api/v1")


# =============================================================================
# API Authentication
# =============================================================================


def api_key_required(f: Callable) -> Callable:
    """Decorator to require API key authentication."""
    from functools import wraps

    @wraps(f)
    def decorated_function(*args: Any, **kwargs: Any) -> Any:
        # Check for API key in header
        api_key = request.headers.get("Authorization", "").replace("Bearer ", "")
        if not api_key:
            api_key = request.headers.get("X-API-Key", "")

        if not api_key:
            raise AuthenticationError("API key required")

        # Validate API key
        from db import get_api_key_by_key

        key_record = get_api_key_by_key(api_key)
        if not key_record:
            raise AuthenticationError("Invalid API key")

        # Store user email in g for the request
        g.api_user_email = key_record["user_email"]
        g.api_key_id = key_record["id"]

        return f(*args, **kwargs)

    return decorated_function


# =============================================================================
# Error Handlers
# =============================================================================


@api_bp.errorhandler(ValidationError)
@api_bp.errorhandler(InvalidGameIDError)
@api_bp.errorhandler(InvalidModListError)
def handle_validation_error(error: ValidationError) -> Any:
    """Handle validation errors."""
    return jsonify(error.to_dict()), error.status_code


@api_bp.errorhandler(AuthenticationError)
def handle_auth_error(error: AuthenticationError) -> Any:
    """Handle authentication errors."""
    return jsonify(error.to_dict()), error.status_code


@api_bp.errorhandler(RateLimitError)
def handle_rate_limit_error(error: RateLimitError) -> Any:
    """Handle rate limit errors."""
    return jsonify(error.to_dict()), error.status_code


@api_bp.errorhandler(AnalysisError)
def handle_analysis_error(error: AnalysisError) -> Any:
    """Handle analysis errors."""
    return jsonify(error.to_dict()), error.status_code


# =============================================================================
# Analysis Endpoints
# =============================================================================


@api_bp.route("/analyze", methods=["POST"])
@rate_limit(limit=30, window=60)  # 30 requests per minute
def analyze() -> Any:
    """
    Analyze a mod list for conflicts and issues.

    Requires API key authentication.

    Request Body:
        {
            "mod_list": "string",  # Newline-separated mod list
            "game": "string"       # Game ID (e.g., "skyrimse")
        }

    Response:
        {
            "success": true,
            "game": "string",
            "mod_count": number,
            "enabled_count": number,
            "conflicts": [...],
            "summary": {...}
        }
    """
    try:
        data = request.get_json()
        if not data:
            raise ValidationError("Request body required")

        mod_list = data.get("mod_list", "")
        game = data.get("game", "skyrimse")

        # Validate inputs
        if not mod_list:
            raise InvalidModListError()

        mod_list = validate_mod_list(mod_list)

        try:
            game = validate_game_id(game)
        except ValueError as e:
            raise InvalidGameIDError(str(e))

        # Perform analysis
        from conflict_detector import ConflictDetector, parse_mod_list_text

        mods = parse_mod_list_text(mod_list)
        detector = ConflictDetector(game)
        analysis = detector.analyze(mods)

        logger.info(
            f"API analysis completed: {len(mods)} mods, {len(analysis.get('conflicts', []))} conflicts",
            extra={"request_id": get_request_id()},
        )

        return jsonify(
            {
                "success": True,
                "game": game,
                "mod_count": len(mods),
                "enabled_count": sum(1 for m in mods if m.get("enabled", True)),
                "conflicts": analysis.get("conflicts", []),
                "summary": analysis.get("summary", {}),
            }
        )

    except (ValidationError, InvalidGameIDError, InvalidModListError) as e:
        raise e
    except Exception as e:
        logger.error(f"API analysis failed: {e}", extra={"request_id": get_request_id()})
        raise AnalysisError(str(e))


# =============================================================================
# Search Endpoints
# =============================================================================


@api_bp.route("/search", methods=["GET"])
@rate_limit(limit=60, window=60)  # 60 requests per minute
def search() -> Any:
    """
    Search for mods in the database.

    Query Parameters:
        q: Search query (required)
        game: Game ID (optional, default: "skyrimse")
        limit: Max results (optional, default: 10, max: 50)
        for_ai: Include AI context (optional, default: false)

    Response:
        {
            "success": true,
            "query": "string",
            "results": [...],
            "total": number
        }
    """
    try:
        query = request.args.get("q", "").strip()
        game = request.args.get("game", "skyrimse")
        limit = request.args.get("limit", "10")
        for_ai = request.args.get("for_ai", "false").lower() == "true"

        if not query:
            raise ValidationError("Search query 'q' is required")

        try:
            game = validate_game_id(game)
        except ValueError as e:
            raise InvalidGameIDError(str(e))

        try:
            limit_int = int(limit)
            limit_int = max(1, min(limit_int, 50))
        except ValueError:
            limit_int = 10

        # Perform search
        from search_engine import get_search_engine

        se = get_search_engine(game)
        results = se.search(query, limit=limit_int, for_ai=for_ai)

        return jsonify(
            {
                "success": True,
                "query": query,
                "game": game,
                "results": results,
                "total": len(results),
            }
        )

    except (ValidationError, InvalidGameIDError) as e:
        raise e
    except Exception as e:
        logger.error(f"API search failed: {e}", extra={"request_id": get_request_id()})
        raise AnalysisError(str(e))


# =============================================================================
# Mod List Endpoints
# =============================================================================


@api_bp.route("/modlist/normalize", methods=["POST"])
@rate_limit(limit=30, window=60)
def normalize_modlist() -> Any:
    """
    Normalize a messy mod list.

    Request Body:
        {
            "mod_list": "string",
            "game": "string"  # optional, default: "skyrimse"
        }

    Response:
        {
            "success": true,
            "normalized": "string",
            "mod_count": number,
            "suggestions": [...]
        }
    """
    try:
        data = request.get_json()
        if not data:
            raise ValidationError("Request body required")

        mod_list = data.get("mod_list", "")
        game = data.get("game", "skyrimse")

        if not mod_list:
            raise InvalidModListError()

        mod_list = validate_mod_list(mod_list)

        try:
            game = validate_game_id(game)
        except ValueError as e:
            raise InvalidGameIDError(str(e))

        # Normalize mod list and generate fuzzy suggestions
        from conflict_detector import ConflictDetector, parse_mod_list_text

        mods = parse_mod_list_text(mod_list)
        normalized = "\n".join(mod["name"] for mod in mods if mod.get("enabled", True))

        # Generate fuzzy matching suggestions for potentially misspelled mods
        suggestions = []
        detector = ConflictDetector(game)
        for mod in mods:
            if mod.get("enabled", True):
                suggestion = detector.parser.get_fuzzy_suggestion(mod["name"])
                if suggestion:
                    suggestions.append(
                        {
                            "original": mod["name"],
                            "suggested": suggestion,
                            "reason": "Possible typo or alternative name",
                        }
                    )

        return jsonify(
            {
                "success": True,
                "normalized": normalized,
                "mod_count": len(mods),
                "suggestions": suggestions,
            }
        )

    except (ValidationError, InvalidModListError) as e:
        raise e
    except Exception as e:
        logger.error(f"Mod list normalization failed: {e}", extra={"request_id": get_request_id()})
        raise AnalysisError(str(e))


# =============================================================================
# Information Endpoints
# =============================================================================


@api_bp.route("/information-map", methods=["GET"])
def information_map() -> Any:
    """
    Get machine-readable map of data flow.

    Response:
        {
            "success": true,
            "data_flow": {
                "inputs": [...],
                "processing": [...],
                "storage": [...],
                "outputs": [...]
            }
        }
    """
    return jsonify(
        {
            "success": True,
            "data_flow": {
                "inputs": [
                    {"name": "mod_list", "type": "text", "description": "User's load order"},
                    {"name": "game", "type": "string", "description": "Target game ID"},
                    {"name": "preferences", "type": "object", "description": "User preferences"},
                ],
                "processing": [
                    {"name": "parsing", "description": "Parse mod list text"},
                    {
                        "name": "conflict_detection",
                        "description": "Detect conflicts using LOOT data",
                    },
                    {"name": "recommendations", "description": "Generate recommendations"},
                ],
                "storage": [
                    {"name": "mod_database", "type": "JSON", "description": "LOOT mod metadata"},
                    {"name": "users.db", "type": "SQLite", "description": "User accounts"},
                    {
                        "name": "community_posts",
                        "type": "SQLite",
                        "description": "Community content",
                    },
                ],
                "outputs": [
                    {"name": "conflicts", "type": "array", "description": "Detected conflicts"},
                    {"name": "recommendations", "type": "array", "description": "Fix suggestions"},
                    {"name": "load_order", "type": "array", "description": "Optimized order"},
                ],
            },
        }
    )


@api_bp.route("/platform-capabilities", methods=["GET"])
def platform_capabilities() -> Any:
    """
    Get runtime capability snapshot.

    Response:
        {
            "success": true,
            "capabilities": {
                "ai_chat": boolean,
                "web_search": boolean,
                "openclaw": boolean,
                "offline_mode": boolean,
                ...
            }
        }
    """
    import os

    from app import AI_CHAT_ENABLED, OFFLINE_MODE, OPENCLAW_ENABLED
    from web_search import web_search_available

    return jsonify(
        {
            "success": True,
            "capabilities": {
                "ai_chat": AI_CHAT_ENABLED,
                "web_search": web_search_available(),
                "openclaw": OPENCLAW_ENABLED,
                "offline_mode": OFFLINE_MODE,
                "payments_enabled": os.environ.get("FLASK_ENV") != "production",
            },
        }
    )


# =============================================================================
# Health Check
# =============================================================================


@api_bp.route("/health", methods=["GET"])
def health_check() -> Any:
    """
    API health check endpoint.

    Response:
        {
            "success": true,
            "status": "healthy",
            "timestamp": "ISO8601"
        }
    """
    from datetime import datetime, timezone

    return jsonify(
        {
            "success": True,
            "status": "healthy",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "version": "1.0.0",
        }
    )
