"""
Logging utilities for SkyModderAI.
Provides structured logging, request tracing, and log filtering.
"""

from __future__ import annotations

import logging
import os
import re
from datetime import datetime, timezone
from functools import wraps
from typing import Any, Callable, Optional

from flask import Flask, request

# =============================================================================
# PII Redaction
# =============================================================================


def redact_email(email: Optional[str]) -> str:
    """
    Redact email for safe logging.

    Args:
        email: Email to redact

    Returns:
        Redacted email (e.g., 'u***@***')
    """
    if not email or not isinstance(email, str):
        return "***"

    e = email.strip().lower()
    if "@" not in e:
        return "***"

    local, domain = e.split("@", 1)
    if len(local) <= 1:
        return "*@***"

    return f"{local[0]}***@{domain[0]}***"


def redact_api_key(key: Optional[str]) -> str:
    """
    Redact API key for safe logging.

    Args:
        key: API key to redact

    Returns:
        Redacted API key (e.g., 'abc1***')
    """
    if not key or not isinstance(key, str):
        return "***"

    key = key.strip()
    if len(key) <= 4:
        return "***"

    return f"{key[:4]}***"


def redact_password(password: Optional[str]) -> str:
    """
    Redact password for safe logging.

    Args:
        password: Password to redact

    Returns:
        Always returns "***"
    """
    return "***"


def redact_customer_id(customer_id: Optional[str]) -> str:
    """
    Redact Stripe customer ID for safe logging.

    Args:
        customer_id: Customer ID to redact

    Returns:
        Redacted customer ID
    """
    if not customer_id or not isinstance(customer_id, str):
        return "***"

    return f"cus_***{customer_id[-4:]}" if customer_id.startswith("cus_") else "***"


# =============================================================================
# Structured Logging
# =============================================================================


class StructuredFormatter(logging.Formatter):
    """
    JSON-like structured formatter for production logging.
    In development, falls back to human-readable format.
    """

    def __init__(
        self,
        fmt: Optional[str] = None,
        datefmt: Optional[str] = None,
        style: str = "%",
        validate: bool = True,
        *,
        defaults: Optional[dict[str, Any]] = None,
    ) -> None:
        super().__init__(fmt, datefmt, style, validate, defaults=defaults)
        self._is_production = os.environ.get("FLASK_ENV") == "production"

    def format(self, record: logging.LogRecord) -> str:
        if self._is_production:
            return self._format_structured(record)
        return super().format(record)

    def _format_structured(self, record: logging.LogRecord) -> str:
        """Format as JSON-like structure for production."""
        import json

        log_data = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # Add extra fields
        for key, value in record.__dict__.items():
            if key not in (
                "name",
                "msg",
                "args",
                "created",
                "filename",
                "funcName",
                "levelname",
                "levelno",
                "lineno",
                "module",
                "msecs",
                "pathname",
                "process",
                "processName",
                "relativeCreated",
                "stack_info",
                "exc_info",
                "exc_text",
                "thread",
                "threadName",
            ):
                log_data[key] = value

        return json.dumps(log_data)


# =============================================================================
# Request Tracing
# =============================================================================


def get_request_id() -> str:
    """
    Get or generate a request ID for tracing.

    Returns:
        Request ID string
    """
    import secrets

    # Check if request ID already exists in context
    if hasattr(request, "request_id"):
        return request.request_id  # type: ignore[attr-defined]

    # Generate new request ID
    request_id = f"req_{secrets.token_hex(8)}"
    request.request_id = request_id  # type: ignore[attr-defined]
    return request_id


def get_request_context() -> dict[str, Any]:
    """
    Get current request context for logging.

    Returns:
        Dictionary with request context
    """
    return {
        "request_id": get_request_id(),
        "method": request.method,
        "path": request.path,
        "remote_addr": request.remote_addr,
        "user_agent": request.headers.get("User-Agent", "")[:100],
    }


class RequestLoggingMiddleware:
    """
    Middleware to log all requests with structured context.
    """

    def __init__(self, app: Flask, logger: Optional[logging.Logger] = None) -> None:
        self.app = app
        self.logger = logger or logging.getLogger(__name__)
        self._setup_middleware()

    def _setup_middleware(self) -> None:
        """Set up before/after request hooks."""

        @self.app.before_request
        def log_request_start() -> None:
            """Log the start of a request."""
            import time

            request.start_time = time.time()  # type: ignore[attr-defined]
            ctx = get_request_context()
            self.logger.info(f"Request started: {request.method} {request.path}", extra=ctx)

        @self.app.after_request
        def log_request_end(response: Any) -> Any:
            """Log the end of a request."""
            import time

            start_time = getattr(request, "start_time", time.time())
            duration_ms = (time.time() - start_time) * 1000

            ctx = get_request_context()
            ctx["status_code"] = response.status_code
            ctx["duration_ms"] = round(duration_ms, 2)
            ctx["response_size"] = response.content_length or 0

            log_level = logging.INFO
            if response.status_code >= 500:
                log_level = logging.ERROR
            elif response.status_code >= 400:
                log_level = logging.WARNING

            self.logger.log(
                log_level,
                f"Request completed: {response.status_code} in {duration_ms:.2f}ms",
                extra=ctx,
            )

            return response


# =============================================================================
# Sensitive Data Filter
# =============================================================================


class SensitiveDataFilter(logging.Filter):
    """
    Filter to redact sensitive data from log records.
    """

    # Patterns to redact
    PATTERNS = [
        # Email addresses
        (r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", "[EMAIL_REDACTED]"),
        # Stripe keys and IDs
        (r"sk_live_[a-zA-Z0-9]{24,}", "[STRIPE_KEY_REDACTED]"),
        (r"sk_test_[a-zA-Z0-9]{24,}", "[STRIPE_KEY_REDACTED]"),
        (r"cus_[a-zA-Z0-9]{14,}", "[CUSTOMER_ID_REDACTED]"),
        (r"sub_[a-zA-Z0-9]{14,}", "[SUBSCRIPTION_ID_REDACTED]"),
        # API keys (generic)
        (r"api_key=[a-zA-Z0-9]{16,}", "api_key=[API_KEY_REDACTED]"),
        # Passwords in URLs
        (r"://[^:]+:[^@]+@", "://[CREDENTIALS_REDACTED]@"),
    ]

    def __init__(self, additional_patterns: Optional[list[tuple[str, str]]] = None) -> None:
        """
        Initialize the filter.

        Args:
            additional_patterns: Additional (pattern, replacement) tuples
        """
        super().__init__()
        self._patterns = self.PATTERNS.copy()
        if additional_patterns:
            self._patterns.extend(additional_patterns)
        self._compiled = [(re.compile(p), r) for p, r in self._patterns]

    def filter(self, record: logging.LogRecord) -> bool:
        """
        Filter the log record, redacting sensitive data.

        Args:
            record: Log record to filter

        Returns:
            Always returns True (record is not dropped)
        """
        # Redact message
        record.msg = self._redact(str(record.msg))

        # Redact args
        if record.args:
            if isinstance(record.args, dict):
                record.args = {k: self._redact(v) for k, v in record.args.items()}
            elif isinstance(record.args, tuple):
                record.args = tuple(self._redact(v) for v in record.args)

        return True

    def _redact(self, text: str) -> str:
        """
        Redact sensitive data from text.

        Args:
            text: Text to redact

        Returns:
            Redacted text
        """
        if not isinstance(text, str):
            return text

        for pattern, replacement in self._compiled:
            text = pattern.sub(replacement, text)

        return text


# =============================================================================
# Convenience Functions
# =============================================================================


def setup_logging(
    level: int = logging.INFO,
    log_file: Optional[str] = None,
    enable_structured: bool = False,
) -> logging.Logger:
    """
    Set up application logging.

    Args:
        level: Logging level
        log_file: Optional log file path
        enable_structured: Enable structured logging for production

    Returns:
        Configured logger
    """
    logger = logging.getLogger("skymodderai")
    logger.setLevel(level)

    # Clear existing handlers
    logger.handlers.clear()

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)

    if enable_structured or os.environ.get("FLASK_ENV") == "production":
        console_handler.setFormatter(StructuredFormatter())
    else:
        console_handler.setFormatter(
            logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
        )

    # Add sensitive data filter
    console_handler.addFilter(SensitiveDataFilter())
    logger.addHandler(console_handler)

    # File handler (optional)
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level)
        file_handler.setFormatter(
            StructuredFormatter()
            if enable_structured
            else logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
        )
        file_handler.addFilter(SensitiveDataFilter())
        logger.addHandler(file_handler)

    return logger


def log_with_context(
    logger: logging.Logger,
    level: int,
    message: str,
    extra_context: Optional[dict[str, Any]] = None,
) -> None:
    """
    Log a message with request context.

    Args:
        logger: Logger instance
        level: Logging level
        message: Log message
        extra_context: Additional context to include
    """
    context = get_request_context()
    if extra_context:
        context.update(extra_context)

    logger.log(level, message, extra=context)


def with_logging(
    logger: Optional[logging.Logger] = None,
    operation: str = "operation",
) -> Callable:
    """
    Decorator to log function execution.

    Args:
        logger: Logger instance (uses root logger if None)
        operation: Operation name for logging

    Returns:
        Decorated function
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            log = logger or logging.getLogger(__name__)
            log.info(f"Starting {operation}: {func.__name__}")

            import time

            start = time.time()
            try:
                result = func(*args, **kwargs)
                duration = (time.time() - start) * 1000
                log.info(f"Completed {operation}: {func.__name__} in {duration:.2f}ms")
                return result
            except Exception as e:
                duration = (time.time() - start) * 1000
                log.error(f"Failed {operation}: {func.__name__} after {duration:.2f}ms - {e}")
                raise

        return wrapper

    return decorator
