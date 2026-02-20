"""
SkyModderAI - Authentication Service

Handles user authentication, registration, and session management business logic.
"""

from __future__ import annotations

import logging
from typing import Any, Optional

from db import (
    create_user,
    get_user_by_email,
    save_user_session,
    verify_user_email,
)
from exceptions import (
    AccountNotVerifiedError,
    DuplicateResourceError,
    InvalidCredentialsError,
    TokenInvalidError,
    UserNotFoundError,
    ValidationError,
)
from security_utils import validate_email, validate_password

logger = logging.getLogger(__name__)


class AuthService:
    """Service for authentication operations."""

    def __init__(self, db_connection: Any) -> None:
        """
        Initialize auth service.

        Args:
            db_connection: Database connection object
        """
        self.db = db_connection

    def register(
        self,
        email: str,
        password: str,
        confirm_password: str,
    ) -> tuple[bool, str]:
        """
        Register a new user.

        Args:
            email: User email
            password: User password
            confirm_password: Password confirmation

        Returns:
            Tuple of (success, message)

        Raises:
            ValidationError: If validation fails
            DuplicateResourceError: If email already registered
        """
        # Validate email
        is_valid, error = validate_email(email)
        if not is_valid:
            raise ValidationError(error)

        # Validate password
        is_valid, error = validate_password(password)
        if not is_valid:
            raise ValidationError(error)

        # Check password match
        if password != confirm_password:
            raise ValidationError("Passwords do not match")

        # Check if user exists
        existing_user = get_user_by_email(email)
        if existing_user:
            raise DuplicateResourceError("Email already registered")

        # Create user
        create_user(email=email, password=password)

        logger.info(f"New user registered: {email}")

        return True, "Registration successful. Please check your email."

    def login(
        self,
        email: str,
        password: str,
        remember: bool = False,
        user_agent: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Authenticate user login.

        Args:
            email: User email
            password: User password
            remember: Remember me flag
            user_agent: User agent string

        Returns:
            User session data

        Raises:
            InvalidCredentialsError: If credentials invalid
            AccountNotVerifiedError: If email not verified
        """
        # Validate email
        is_valid, error = validate_email(email)
        if not is_valid:
            raise InvalidCredentialsError()

        # Get user
        user = get_user_by_email(email)
        if not user:
            raise InvalidCredentialsError()

        # Check password
        if not user.get("password_hash"):
            raise InvalidCredentialsError()

        from werkzeug.security import check_password_hash

        if not check_password_hash(user["password_hash"], password):
            raise InvalidCredentialsError()

        # Check email verification
        if not user.get("email_verified"):
            raise AccountNotVerifiedError()

        # Save session
        save_user_session(
            email=email,
            user_agent=user_agent or "",
            remember=remember,
        )

        logger.info(f"User logged in: {email}")

        return {
            "email": email,
            "tier": user.get("tier", "free"),
            "email_verified": True,
        }

    def verify_email(self, token: str) -> tuple[bool, str]:
        """
        Verify user email with token.

        Args:
            token: Verification token

        Returns:
            Tuple of (success, message)

        Raises:
            TokenInvalidError: If token invalid
            TokenExpiredError: If token expired
            UserNotFoundError: If user not found
        """
        from auth_utils import verify_verification_token

        email = verify_verification_token(token)
        if not email:
            raise TokenInvalidError()

        # Verify email
        verify_user_email(email)

        logger.info(f"Email verified: {email}")

        return True, "Email verified successfully"

    def logout(self, email: str) -> None:
        """
        Log out user.

        Args:
            email: User email
        """
        logger.info(f"User logged out: {email}")

    def get_user(self, email: str) -> Optional[dict[str, Any]]:
        """
        Get user by email.

        Args:
            email: User email

        Returns:
            User data or None
        """
        return get_user_by_email(email)

    def send_verification_email(self, email: str) -> tuple[bool, str]:
        """
        Send email verification email.

        Args:
            email: User email

        Returns:
            Tuple of (success, message)

        Raises:
            UserNotFoundError: If user not found
        """
        user = get_user_by_email(email)
        if not user:
            raise UserNotFoundError()

        from auth_utils import send_verification_email

        send_verification_email(email)

        return True, "Verification email sent"

    def get_user_sessions(self, email: str) -> list[dict[str, Any]]:
        """
        Get active sessions for user.

        Args:
            email: User email

        Returns:
            List of session data
        """
        from db import get_user_sessions

        return get_user_sessions(email)

    def revoke_session(self, email: str, token: str) -> bool:
        """
        Revoke a user session.

        Args:
            email: User email
            token: Session token

        Returns:
            True if revoked
        """
        from db import revoke_session

        return revoke_session(token)
