"""
SkyModderAI - Custom Exception Hierarchy

Professional-grade error handling with specific exception types for different error scenarios.
"""

from __future__ import annotations

from typing import Any, Dict, Optional


class SkyModderAIError(Exception):
    """Base exception for all SkyModderAI exceptions."""

    def __init__(
        self,
        message: str,
        error_code: str = "UNKNOWN_ERROR",
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None,
    ):
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)

    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for JSON response."""
        return {
            "error": self.message,
            "error_code": self.error_code,
            "status_code": self.status_code,
            "details": self.details,
        }


# =============================================================================
# Authentication & Authorization Errors (401, 403)
# =============================================================================


class AuthenticationError(SkyModderAIError):
    """Raised when authentication fails."""

    def __init__(
        self,
        message: str = "Authentication required",
        error_code: str = "AUTH_REQUIRED",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, error_code, 401, details)


class InvalidCredentialsError(SkyModderAIError):
    """Raised when credentials are invalid."""

    def __init__(
        self,
        message: str = "Invalid email or password",
        error_code: str = "INVALID_CREDENTIALS",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, error_code, 401, details)


class TokenExpiredError(SkyModderAIError):
    """Raised when a token has expired."""

    def __init__(
        self,
        message: str = "Token has expired",
        error_code: str = "TOKEN_EXPIRED",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, error_code, 401, details)


class TokenInvalidError(SkyModderAIError):
    """Raised when a token is invalid."""

    def __init__(
        self,
        message: str = "Invalid token",
        error_code: str = "TOKEN_INVALID",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, error_code, 401, details)


class AuthorizationError(SkyModderAIError):
    """Raised when user lacks permission."""

    def __init__(
        self,
        message: str = "You do not have permission to access this resource",
        error_code: str = "FORBIDDEN",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, error_code, 403, details)


class AccountNotVerifiedError(SkyModderAIError):
    """Raised when account email is not verified."""

    def __init__(
        self,
        message: str = "Please verify your email address",
        error_code: str = "ACCOUNT_NOT_VERIFIED",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, error_code, 403, details)


# =============================================================================
# Validation Errors (400)
# =============================================================================


class ValidationError(SkyModderAIError):
    """Base class for validation errors."""

    def __init__(
        self,
        message: str = "Validation failed",
        error_code: str = "VALIDATION_ERROR",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, error_code, 400, details)


class InvalidEmailError(ValidationError):
    """Raised when email format is invalid."""

    def __init__(
        self,
        message: str = "Invalid email format",
        error_code: str = "INVALID_EMAIL",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, error_code, details)


class InvalidPasswordError(ValidationError):
    """Raised when password doesn't meet requirements."""

    def __init__(
        self,
        message: str = "Password does not meet requirements",
        error_code: str = "INVALID_PASSWORD",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, error_code, details)


class InvalidGameIDError(ValidationError):
    """Raised when game ID is invalid."""

    def __init__(
        self,
        message: str = "Invalid game ID",
        error_code: str = "INVALID_GAME_ID",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, error_code, details)


class InvalidModListError(ValidationError):
    """Raised when mod list is invalid."""

    def __init__(
        self,
        message: str = "Invalid mod list",
        error_code: str = "INVALID_MOD_LIST",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, error_code, details)


class InputTooLargeError(ValidationError):
    """Raised when input exceeds size limits."""

    def __init__(
        self,
        message: str = "Input exceeds maximum size limit",
        error_code: str = "INPUT_TOO_LARGE",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, error_code, details)


# =============================================================================
# Resource Errors (404, 409)
# =============================================================================


class ResourceNotFoundError(SkyModderAIError):
    """Raised when a resource is not found."""

    def __init__(
        self,
        message: str = "Resource not found",
        error_code: str = "NOT_FOUND",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, error_code, 404, details)


class UserNotFoundError(ResourceNotFoundError):
    """Raised when user is not found."""

    def __init__(
        self,
        message: str = "User not found",
        error_code: str = "USER_NOT_FOUND",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, error_code, details)


class ModNotFoundError(ResourceNotFoundError):
    """Raised when a mod is not found."""

    def __init__(
        self,
        message: str = "Mod not found",
        error_code: str = "MOD_NOT_FOUND",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, error_code, details)


class ConflictError(SkyModderAIError):
    """Raised when there's a resource conflict."""

    def __init__(
        self,
        message: str = "Resource conflict",
        error_code: str = "CONFLICT",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, error_code, 409, details)


class DuplicateResourceError(ConflictError):
    """Raised when trying to create a duplicate resource."""

    def __init__(
        self,
        message: str = "Resource already exists",
        error_code: str = "DUPLICATE_RESOURCE",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, error_code, details)


# =============================================================================
# Analysis & Processing Errors (500, 503)
# =============================================================================


class AnalysisError(SkyModderAIError):
    """Base class for analysis-related errors."""

    def __init__(
        self,
        message: str = "Analysis failed",
        error_code: str = "ANALYSIS_ERROR",
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, error_code, status_code, details)


class ConflictDetectionError(AnalysisError):
    """Raised when conflict detection fails."""

    def __init__(
        self,
        message: str = "Failed to detect conflicts",
        error_code: str = "CONFLICT_DETECTION_FAILED",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, error_code, 500, details)


class LOOTParserError(AnalysisError):
    """Raised when LOOT parsing fails."""

    def __init__(
        self,
        message: str = "Failed to parse LOOT data",
        error_code: str = "LOOT_PARSER_ERROR",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, error_code, 500, details)


class DataNotAvailableError(AnalysisError):
    """Raised when required data is not available."""

    def __init__(
        self,
        message: str = "Required data is not available",
        error_code: str = "DATA_NOT_AVAILABLE",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, error_code, 503, details)


# =============================================================================
# OpenCLAW Errors (400, 500)
# =============================================================================


class OpenClawError(SkyModderAIError):
    """Base class for OpenCLAW-related errors."""

    def __init__(
        self,
        message: str = "OpenCLAW operation failed",
        error_code: str = "OPENCLAW_ERROR",
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, error_code, status_code, details)


class SandboxError(OpenClawError):
    """Raised when sandbox operation fails."""

    def __init__(
        self,
        message: str = "Sandbox operation failed",
        error_code: str = "SANDBOX_ERROR",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, error_code, 500, details)


class PathTraversalError(SandboxError):
    """Raised when path traversal is detected."""

    def __init__(
        self,
        message: str = "Path traversal detected",
        error_code: str = "PATH_TRAVERSAL",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, error_code, 400, details)


class PermissionDeniedError(OpenClawError):
    """Raised when permission is denied."""

    def __init__(
        self,
        message: str = "Permission denied",
        error_code: str = "PERMISSION_DENIED",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, error_code, 403, details)


class PlanExecutionError(OpenClawError):
    """Raised when plan execution fails."""

    def __init__(
        self,
        message: str = "Plan execution failed",
        error_code: str = "PLAN_EXECUTION_FAILED",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, error_code, 500, details)


class SafetyViolationError(OpenClawError):
    """Raised when safety check fails."""

    def __init__(
        self,
        message: str = "Safety check failed",
        error_code: str = "SAFETY_VIOLATION",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, error_code, 400, details)


# =============================================================================
# Rate Limiting & API Errors (429, 503)
# =============================================================================


class RateLimitError(SkyModderAIError):
    """Raised when rate limit is exceeded."""

    def __init__(
        self,
        message: str = "Rate limit exceeded",
        error_code: str = "RATE_LIMIT_EXCEEDED",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, error_code, 429, details)


class ServiceUnavailableError(SkyModderAIError):
    """Raised when service is unavailable."""

    def __init__(
        self,
        message: str = "Service temporarily unavailable",
        error_code: str = "SERVICE_UNAVAILABLE",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, error_code, 503, details)


# =============================================================================
# Database Errors (500)
# =============================================================================


class DatabaseError(SkyModderAIError):
    """Base class for database errors."""

    def __init__(
        self,
        message: str = "Database operation failed",
        error_code: str = "DATABASE_ERROR",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, error_code, 500, details)


class DatabaseConnectionError(DatabaseError):
    """Raised when database connection fails."""

    def __init__(
        self,
        message: str = "Failed to connect to database",
        error_code: str = "DATABASE_CONNECTION_FAILED",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, error_code, details)


class DatabaseOperationError(DatabaseError):
    """Raised when database operation fails."""

    def __init__(
        self,
        message: str = "Database operation failed",
        error_code: str = "DATABASE_OPERATION_FAILED",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, error_code, details)
