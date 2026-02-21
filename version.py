"""
SkyModderAI - Version Information

Centralized version management for the application.
"""

__version__ = "1.0.0-beta"
__version_info__ = (1, 0, 0, "beta")

# Version components
VERSION_MAJOR = 1
VERSION_MINOR = 0
VERSION_PATCH = 0
VERSION_STATUS = "beta"

# Application info
__app_name__ = "SkyModderAI"
__description__ = "AI-powered mod compatibility checker for Bethesda games"
__author__ = "SkyModderAI Community"
__license__ = "MIT"

# Build information
__build_date__ = "2026-02-21"
__python_requires__ = ">=3.11"


def get_version() -> str:
    """Get the full version string."""
    return __version__


def get_version_info() -> dict:
    """Get detailed version information."""
    return {
        "version": __version__,
        "version_info": __version_info__,
        "major": VERSION_MAJOR,
        "minor": VERSION_MINOR,
        "patch": VERSION_PATCH,
        "status": VERSION_STATUS,
        "app_name": __app_name__,
        "python_requires": __python_requires__,
        "build_date": __build_date__,
    }


def check_python_version() -> bool:
    """Check if running on required Python version."""
    import sys

    current = sys.version_info
    required = (3, 11)

    if current[:2] < required:
        return False
    return True
