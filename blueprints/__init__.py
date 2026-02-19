"""
SkyModderAI - Blueprint Package
"""

from __future__ import annotations

from .analysis import analysis_bp
from .api import api_bp
from .auth import auth_bp
from .business import business_bp
from .community import community_bp
from .export import export_bp
from .feedback import feedback_bp
from .openclaw import openclaw_bp
from .shopping import shopping_bp
from .sponsors import sponsors_bp

__all__ = [
    "auth_bp",
    "api_bp",
    "analysis_bp",
    "community_bp",
    "openclaw_bp",
    "feedback_bp",
    "export_bp",
    "sponsors_bp",
    "business_bp",
    "shopping_bp",
]
