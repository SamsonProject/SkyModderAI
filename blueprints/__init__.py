"""
SkyModderAI - Blueprint Package
"""
from __future__ import annotations

from .auth import auth_bp
from .api import api_bp
from .analysis import analysis_bp
from .community import community_bp
from .openclaw import openclaw_bp

__all__ = [
    "auth_bp",
    "api_bp",
    "analysis_bp",
    "community_bp",
    "openclaw_bp",
]
