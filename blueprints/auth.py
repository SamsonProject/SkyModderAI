"""
SkyModderAI - Authentication Blueprint

Handles user authentication, registration, email verification, and session management.
"""

from __future__ import annotations

import logging
from functools import wraps
from typing import TYPE_CHECKING, Any, Callable

from flask import (
    Blueprint,
    current_app,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

from auth_utils import verify_verification_token
from config import config
from db import get_user_by_email, save_user_session
from exceptions import (
    AccountNotVerifiedError,
    AuthenticationError,
    DuplicateResourceError,
    InvalidCredentialsError,
    TokenExpiredError,
    TokenInvalidError,
    UserNotFoundError,
    ValidationError,
)
from logging_utils import get_request_id
from oauth_utils import (
    github_oauth_callback,
    github_oauth_init,
    google_oauth_callback,
    google_oauth_init,
)
from security_utils import validate_email, validate_password

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)

# Create blueprint
auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


# =============================================================================
# Authentication Decorators
# =============================================================================


def login_required(f: Callable) -> Callable:
    """Decorator to require authentication for a route."""

    @wraps(f)
    def decorated_function(*args: Any, **kwargs: Any) -> Any:
        if "user_email" not in session:
            if request.is_json:
                raise AuthenticationError()
            flash("Please log in to access this page.", "warning")
            return redirect(url_for("auth.login"))
        return f(*args, **kwargs)

    return decorated_function


def verified_email_required(f: Callable) -> Callable:
    """Decorator to require verified email for a route."""

    @wraps(f)
    def decorated_function(*args: Any, **kwargs: Any) -> Any:
        if "user_email" not in session:
            raise AuthenticationError()

        user = get_user_by_email(session["user_email"])
        if not user:
            raise UserNotFoundError()
        if not user.get("email_verified"):
            raise AccountNotVerifiedError()

        return f(*args, **kwargs)

    return decorated_function


# =============================================================================
# Authentication Routes
# =============================================================================


@auth_bp.route("/login", methods=["GET", "POST"])
def login() -> Any:
    """Handle user login."""
    if request.method == "GET":
        return render_template("auth.html")

    # POST: Handle login form submission
    data = request.get_json(silent=True) or request.form
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")
    remember = data.get("remember", False)

    try:
        # Validate input
        is_valid, error = validate_email(email)
        if not is_valid:
            raise ValidationError(error)

        if not password:
            raise ValidationError("Password is required")

        # Get user from database
        user = get_user_by_email(email)
        if not user:
            raise InvalidCredentialsError()

        # Check password
        if not user.get("password_hash"):
            raise InvalidCredentialsError()

        from werkzeug.security import check_password_hash

        if not check_password_hash(user["password_hash"], password):
            raise InvalidCredentialsError()

        # Check if email is verified
        if not user.get("email_verified"):
            raise AccountNotVerifiedError()

        # Create session
        session.permanent = True
        session["user_email"] = email
        session["user_tier"] = user.get("tier", "free")

        # Save session to database for device management
        save_user_session(
            email=email,
            user_agent=request.headers.get("User-Agent", ""),
            remember=remember,
        )

        logger.info(f"User logged in: {email}", extra={"request_id": get_request_id()})

        if request.is_json:
            return jsonify({"success": True, "message": "Login successful"})

        next_page = request.args.get("next")
        if next_page:
            return redirect(next_page)
        return redirect(url_for("index"))

    except (AccountNotVerifiedError, InvalidCredentialsError, ValidationError) as e:
        if request.is_json:
            return jsonify(e.to_dict()), e.status_code
        flash(str(e), "error")
        return render_template("auth.html"), 401


@auth_bp.route("/signup", methods=["POST"])
def signup() -> Any:
    """Handle user registration."""
    data = request.get_json(silent=True) or request.form
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")
    confirm_password = data.get("confirm_password", "")

    try:
        # Validate input
        is_valid, error = validate_email(email)
        if not is_valid:
            raise ValidationError(error)

        is_valid, error = validate_password(password)
        if not is_valid:
            raise ValidationError(error)

        if password != confirm_password:
            raise ValidationError("Passwords do not match")

        # Check if user already exists
        existing_user = get_user_by_email(email)
        if existing_user:
            raise DuplicateResourceError("Email already registered")

        # Create user
        from db import ensure_user_unverified

        ensure_user_unverified(email=email, password=password)

        # Send verification email (optional - gracefully handle email sending failures)
        try:
            from urllib.parse import urljoin

            from flask import url_for

            from app import make_verification_token, send_verification_email

            token = make_verification_token(email)
            base_url = request.host_url.rstrip("/")
            verify_url = urljoin(base_url + "/", f"verify-email?token={token}")
            send_verification_email(email, verify_url)
        except Exception as e:
            # Log the error but don't fail registration
            logger.warning(f"Failed to send verification email to {email}: {e}")

        logger.info(f"New user registered: {email}", extra={"request_id": get_request_id()})

        if request.is_json:
            return jsonify(
                {"success": True, "message": "Registration successful. Please check your email."}
            )

        flash("Registration successful! Please check your email to verify your account.", "success")
        return redirect(url_for("auth.login"))

    except (DuplicateResourceError, ValidationError) as e:
        if request.is_json:
            return jsonify(e.to_dict()), e.status_code
        flash(str(e), "error")
        return render_template("auth.html"), 400


@auth_bp.route("/logout")
def logout() -> Any:
    """Handle user logout."""
    email = session.get("user_email")
    if email:
        logger.info(f"User logged out: {email}", extra={"request_id": get_request_id()})

    session.clear()
    response = redirect(url_for("index"))

    if request.is_json:
        return jsonify({"success": True, "message": "Logout successful"})

    return response


@auth_bp.route("/verify/<token>")
def verify_email(token: str) -> Any:
    """Verify user email address."""
    try:
        email = verify_verification_token(token)
        if not email:
            raise TokenInvalidError()

        # Mark email as verified
        from db import verify_user_email

        verify_user_email(email)

        logger.info(f"Email verified: {email}", extra={"request_id": get_request_id()})

        flash("Email verified successfully! You can now log in.", "success")
        return render_template("verified.html", success=True)

    except (TokenInvalidError, TokenExpiredError) as e:
        flash(str(e), "error")
        return render_template("verified.html", success=False), 400


# =============================================================================
# OAuth Routes
# =============================================================================


@auth_bp.route("/google")
def google_login() -> Any:
    """Initiate Google OAuth login."""
    if not config.GOOGLE_OAUTH_ENABLED:
        flash("Google login is not enabled.", "error")
        return redirect(url_for("auth.login"))

    return google_oauth_init()


@auth_bp.route("/google/callback")
def google_callback() -> Any:
    """Handle Google OAuth callback."""
    try:
        email = google_oauth_callback()
        if not email:
            raise AuthenticationError("Failed to authenticate with Google")

        # Create or update user
        user = get_user_by_email(email)
        if not user:
            from db import create_user

            create_user(email=email, email_verified=True)
        elif not user.get("email_verified"):
            from db import verify_user_email

            verify_user_email(email)

        # Create session
        session.permanent = True
        session["user_email"] = email
        session["user_tier"] = "free"

        logger.info(f"User logged in via Google: {email}", extra={"request_id": get_request_id()})

        return redirect(url_for("index"))

    except Exception as e:
        logger.error(f"Google OAuth callback failed: {e}", extra={"request_id": get_request_id()})
        flash("Google login failed. Please try again.", "error")
        return redirect(url_for("auth.login"))


@auth_bp.route("/github")
def github_login() -> Any:
    """Initiate GitHub OAuth login."""
    if not config.GITHUB_OAUTH_ENABLED:
        flash("GitHub login is not enabled.", "error")
        return redirect(url_for("auth.login"))

    return github_oauth_init()


@auth_bp.route("/github/callback")
def github_callback() -> Any:
    """Handle GitHub OAuth callback."""
    try:
        email = github_oauth_callback()
        if not email:
            raise AuthenticationError("Failed to authenticate with GitHub")

        # Create or update user
        user = get_user_by_email(email)
        if not user:
            from db import create_user

            create_user(email=email, email_verified=True)
        elif not user.get("email_verified"):
            from db import verify_user_email

            verify_user_email(email)

        # Create session
        session.permanent = True
        session["user_email"] = email
        session["user_tier"] = "free"

        logger.info(f"User logged in via GitHub: {email}", extra={"request_id": get_request_id()})

        return redirect(url_for("index"))

    except Exception as e:
        logger.error(f"GitHub OAuth callback failed: {e}", extra={"request_id": get_request_id()})
        flash("GitHub login failed. Please try again.", "error")
        return redirect(url_for("auth.login"))


# =============================================================================
# Session Management
# =============================================================================


@auth_bp.route("/session/refresh", methods=["POST"])
@login_required
def refresh_session() -> Any:
    """Refresh user session."""
    email = session.get("user_email")
    if email:
        session.permanent = True
        save_user_session(
            email=email,
            user_agent=request.headers.get("User-Agent", ""),
            remember=True,
        )

    if request.is_json:
        return jsonify({"success": True, "message": "Session refreshed"})

    flash("Session refreshed.", "success")
    return redirect(url_for("index"))


# =============================================================================
# Password Reset
# =============================================================================


@auth_bp.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    """Request password reset email."""
    import secrets
    import time

    from itsdangerous import URLSafeTimedSerializer

    from constants import PASSWORD_RESET_TOKEN_MAX_AGE
    from db import create_password_reset_token, get_user_by_email

    if request.method == "POST":
        data = request.get_json(silent=True) or request.form
        email = data.get("email", "").strip().lower()

        if not email:
            if request.is_json:
                return jsonify({"error": "Email is required"}), 400
            flash("Email is required", "error")
            return render_template("forgot-password.html")

        # Check if user exists
        user = get_user_by_email(email)
        if not user:
            # Don't reveal if email exists - show success either way
            if request.is_json:
                return jsonify(
                    {"success": True, "message": "If that email exists, we've sent a reset link."}
                )
            flash("If that email exists, we've sent a password reset link.", "info")
            return render_template("forgot-password-sent.html")

        # Generate reset token
        secret_key = current_app.config["SECRET_KEY"]
        s = URLSafeTimedSerializer(secret_key, salt="password-reset")
        token = s.dumps({"email": email, "rnd": secrets.token_hex(16)})

        # Calculate expiry timestamp
        expires_at = int(time.time()) + PASSWORD_RESET_TOKEN_MAX_AGE

        # Store token in database
        create_password_reset_token(email, token, expires_at)

        # Send email (if configured)
        try:
            reset_link = url_for("auth.reset_password", token=token, _external=True)
            # Email sending would go here if SMTP is configured
            logger.info(f"Password reset requested for {email}: {reset_link}")
        except Exception as e:
            logger.error(f"Failed to create reset link: {e}")

        if request.is_json:
            return jsonify(
                {"success": True, "message": "If that email exists, we've sent a reset link."}
            )
        flash("If that email exists, we've sent a password reset link.", "info")
        return render_template("forgot-password-sent.html")

    # GET - show form
    return render_template("forgot-password.html")


@auth_bp.route("/reset-password", methods=["GET", "POST"])
def reset_password():
    """Reset password with token from email."""
    from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

    from constants import PASSWORD_RESET_TOKEN_MAX_AGE
    from db import get_password_reset_token, reset_user_password, use_password_reset_token

    token = request.args.get("token", "")
    if not token:
        flash("Missing reset token", "error")
        return redirect(url_for("auth.forgot_password"))

    # Verify token signature
    secret_key = current_app.config["SECRET_KEY"]
    s = URLSafeTimedSerializer(secret_key, salt="password-reset")
    try:
        token_data = s.loads(token, max_age=PASSWORD_RESET_TOKEN_MAX_AGE)
        email = token_data.get("email")
    except (BadSignature, SignatureExpired):
        flash("Invalid or expired reset link", "error")
        return redirect(url_for("auth.forgot_password"))

    if not email:
        flash("Invalid reset link", "error")
        return redirect(url_for("auth.forgot_password"))

    # Verify token exists in database and is valid
    token_row = get_password_reset_token(token)
    if not token_row:
        flash("Invalid or expired reset link", "error")
        return redirect(url_for("auth.forgot_password"))

    if request.method == "POST":
        data = request.get_json(silent=True) or request.form
        password = data.get("password", "")
        confirm = data.get("confirm_password", "")

        # Validate password
        if len(password) < 8:
            if request.is_json:
                return jsonify({"error": "Password must be at least 8 characters"}), 400
            flash("Password must be at least 8 characters", "error")
            return render_template("reset-password.html", token=token)

        if password != confirm:
            if request.is_json:
                return jsonify({"error": "Passwords do not match"}), 400
            flash("Passwords do not match", "error")
            return render_template("reset-password.html", token=token)

        # Reset password
        if reset_user_password(email, password):
            # Invalidate the token
            use_password_reset_token(token)

            if request.is_json:
                return jsonify({"success": True, "message": "Password reset successfully"})
            flash("Password reset successfully. Please log in.", "success")
            return redirect(url_for("auth.login"))
        else:
            if request.is_json:
                return jsonify({"error": "Failed to reset password"}), 500
            flash("Failed to reset password. Please try again.", "error")

    # GET - show form
    return render_template("reset-password.html", token=token, email=email)
