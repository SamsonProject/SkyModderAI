"""
SkyModderAI - Sentry Integration

Production error tracking and performance monitoring.
"""
from __future__ import annotations

import logging
import os
from typing import TYPE_CHECKING, Any, Optional

import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration
from sentry_sdk.integrations.logging import LoggingIntegration

if TYPE_CHECKING:
    from flask import Flask

logger = logging.getLogger(__name__)


def init_sentry(app: Optional["Flask"] = None) -> bool:
    """
    Initialize Sentry SDK for error tracking.

    Args:
        app: Flask application instance (optional)

    Returns:
        True if Sentry initialized successfully
    """
    dsn = os.environ.get("SENTRY_DSN")

    if not dsn:
        logger.info("Sentry DSN not set - error tracking disabled")
        return False

    try:
        # Configure Sentry
        sentry_sdk.init(
            dsn=dsn,
            integrations=[
                FlaskIntegration(),
                LoggingIntegration(
                    level=logging.INFO,  # Capture info and above as breadcrumbs
                    event_level=logging.ERROR,  # Send errors as events
                ),
            ],
            # Performance monitoring
            traces_sample_rate=_get_traces_sample_rate(),
            # Profiling
            profiles_sample_rate=_get_profiles_sample_rate(),
            # Release tracking
            release=os.environ.get("SENTRY_RELEASE", "dev"),
            environment=os.environ.get("FLASK_ENV", "development"),
            # Error sampling
            send_default_pii=False,  # Don't send personal data
            # Breadcrumbs
            max_breadcrumbs=50,
            # Attach stacktrace
            attach_stacktrace=True,
        )

        # Set Flask app context if provided
        if app:
            _configure_flask_app(app)

        logger.info(f"Sentry initialized for environment: {os.environ.get('FLASK_ENV', 'dev')}")
        return True

    except Exception as e:
        logger.error(f"Failed to initialize Sentry: {e}")
        return False


def _get_traces_sample_rate() -> float:
    """Get trace sample rate based on environment."""
    env = os.environ.get("FLASK_ENV", "development")

    if env == "production":
        return float(os.environ.get("SENTRY_TRACES_SAMPLE_RATE", "0.1"))
    elif env == "staging":
        return float(os.environ.get("SENTRY_TRACES_SAMPLE_RATE", "0.5"))
    else:
        return float(os.environ.get("SENTRY_TRACES_SAMPLE_RATE", "1.0"))


def _get_profiles_sample_rate() -> float:
    """Get profile sample rate based on environment."""
    env = os.environ.get("FLASK_ENV", "development")

    if env == "production":
        return float(os.environ.get("SENTRY_PROFILES_SAMPLE_RATE", "0.05"))
    elif env == "staging":
        return float(os.environ.get("SENTRY_PROFILES_SAMPLE_RATE", "0.2"))
    else:
        return 0.0  # Disable profiling in development


def _configure_flask_app(app: "Flask") -> None:
    """Configure Flask-specific Sentry settings."""

    @app.before_request
    def sentry_before_request() -> None:
        """Set transaction name for requests."""
        from flask import request

        sentry_sdk.set_transaction_name(f"{request.method} {request.endpoint}")
        sentry_sdk.set_tag("request_id", request.headers.get("X-Request-ID", "unknown"))

    @app.after_request
    def sentry_after_request(response: Any) -> Any:
        """Add Sentry trace header to response."""
        from flask import request

        # Get trace IDs for correlation
        trace_id = sentry_sdk.get_current_span().trace_id
        span_id = sentry_sdk.get_current_span().span_id

        response.headers["X-Sentry-Trace"] = f"{trace_id}-{span_id}"

        return response


def capture_exception(exception: Exception, **kwargs: Any) -> Optional[str]:
    """
    Capture an exception to Sentry.

    Args:
        exception: Exception to capture
        **kwargs: Additional context

    Returns:
        Event ID if captured, None otherwise
    """
    try:
        with sentry_sdk.configure_scope() as scope:
            for key, value in kwargs.items():
                scope.set_extra(key, value)

        return sentry_sdk.capture_exception(exception)
    except Exception as e:
        logger.error(f"Failed to capture exception: {e}")
        return None


def capture_message(message: str, level: str = "info", **kwargs: Any) -> Optional[str]:
    """
    Capture a message to Sentry.

    Args:
        message: Message to capture
        level: Log level (info, warning, error)
        **kwargs: Additional context

    Returns:
        Event ID if captured, None otherwise
    """
    try:
        with sentry_sdk.configure_scope() as scope:
            for key, value in kwargs.items():
                scope.set_extra(key, value)

        return sentry_sdk.capture_message(message, level=level)
    except Exception as e:
        logger.error(f"Failed to capture message: {e}")
        return None


def set_user_context(user_id: str, email: Optional[str] = None, **kwargs: Any) -> None:
    """
    Set user context for error tracking.

    Args:
        user_id: User identifier
        email: User email (will be redacted)
        **kwargs: Additional user data
    """
    try:
        sentry_sdk.set_user(
            {
                "id": user_id,
                "email": _redact_email(email) if email else None,
                **kwargs,
            }
        )
    except Exception as e:
        logger.error(f"Failed to set user context: {e}")


def _redact_email(email: str) -> str:
    """Redact email for Sentry."""
    if "@" not in email:
        return "***"
    local, domain = email.split("@", 1)
    return f"{local[0]}***@{domain[0]}***"


def add_breadcrumb(message: str, category: str = "default", **kwargs: Any) -> None:
    """
    Add a breadcrumb for context.

    Args:
        message: Breadcrumb message
        category: Breadcrumb category
        **kwargs: Additional data
    """
    try:
        sentry_sdk.add_breadcrumb(message=message, category=category, **kwargs)
    except Exception as e:
        logger.error(f"Failed to add breadcrumb: {e}")
