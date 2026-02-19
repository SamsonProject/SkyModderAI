"""
OAuth utility functions for Google and GitHub authentication.
This module handles OAuth flows and token management.
"""

import json
from urllib.parse import urlencode, urljoin

import requests
from flask import current_app, redirect, request, url_for

# Import auth utilities
from auth_utils import make_state_token, verify_state_token

# Import configuration
from config import config

# Import database functions
from db import ensure_user_unverified, session_create, set_user_verified


# Google OAuth functions
def _google_oauth_state_make(next_url=""):
    """Generate a signed state token for Google OAuth."""
    return make_state_token(
        secret_key=config.SECRET_KEY, salt="google-oauth-state", next_url=next_url
    )


def _google_oauth_state_verify(state):
    """Verify the state token from Google OAuth."""
    return verify_state_token(secret_key=config.SECRET_KEY, salt="google-oauth-state", state=state)


# Aliases for compatibility
def google_oauth_init():
    """Alias for google_oauth_authorize."""
    return google_oauth_authorize()


def github_oauth_init():
    """Alias for github_oauth_authorize."""
    return github_oauth_authorize()


def google_oauth_authorize():
    """Redirect to Google OAuth consent page."""
    if not config.GOOGLE_OAUTH_ENABLED:
        current_app.logger.warning("Google OAuth not enabled")
        return redirect(url_for("login"))

    next_url = (request.args.get("next") or "").strip()
    if next_url and (not next_url.startswith("/") or "//" in next_url):
        next_url = ""

    state = _google_oauth_state_make(next_url)
    redirect_uri = urljoin(config.BASE_URL + "/", "auth/google/callback")

    params = {
        "client_id": config.GOOGLE_CLIENT_ID,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": "openid email profile",
        "state": state,
        "access_type": "offline",
        "prompt": "select_account",
    }

    url = "https://accounts.google.com/o/oauth2/v2/auth?" + urlencode(params)
    return redirect(url)


def google_oauth_callback():
    """Handle Google OAuth callback and authenticate user."""
    if not config.GOOGLE_OAUTH_ENABLED:
        current_app.logger.warning("Google OAuth not enabled")
        return redirect(url_for("login"))

    code = request.args.get("code")
    state = request.args.get("state")
    payload = _google_oauth_state_verify(state)

    if not code or not payload:
        current_app.logger.warning("Missing code or state in Google OAuth callback")
        return redirect(url_for("login", error="google_oauth_failed"))

    redirect_uri = urljoin(config.BASE_URL + "/", "auth/google/callback")

    try:
        # Exchange authorization code for access token
        token_resp = requests.post(
            "https://oauth2.googleapis.com/token",
            data={
                "code": code,
                "client_id": config.GOOGLE_CLIENT_ID,
                "client_secret": config.GOOGLE_CLIENT_SECRET,
                "redirect_uri": redirect_uri,
                "grant_type": "authorization_code",
            },
            headers={"Accept": "application/json"},
            timeout=15,
        )

        if token_resp.status_code != 200:
            current_app.logger.warning(f"Google token exchange failed: {token_resp.status_code}")
            return redirect(url_for("login", error="google_oauth_failed"))

        try:
            token_data = token_resp.json()
            access_token = token_data.get("access_token")
            if not access_token:
                raise ValueError("No access token in response")

            # Get user info
            user_resp = requests.get(
                "https://www.googleapis.com/oauth2/v2/userinfo",
                headers={"Authorization": f"Bearer {access_token}"},
                timeout=10,
            )

            if user_resp.status_code != 200:
                current_app.logger.warning(f"Google userinfo failed: {user_resp.status_code}")
                return redirect(url_for("login", error="google_oauth_failed"))

            user_data = user_resp.json()
            email = (user_data.get("email") or "").strip().lower()
            if not email or "@" not in email:
                current_app.logger.warning("Invalid email from Google OAuth")
                return redirect(url_for("login", error="google_oauth_failed"))

            # Create/update user and log them in
            ensure_user_unverified(email, password=None)
            set_user_verified(email)

            # Create session
            sess_token, max_age = session_create(
                email, remember_me=True, user_agent=request.headers.get("User-Agent")
            )

            # Determine redirect URL
            next_url = (payload.get("next") or "").strip()
            if not next_url or not next_url.startswith("/") or "//" in next_url:
                next_url = url_for("index")

            # Set session cookie and redirect
            resp = redirect(next_url)
            if sess_token:
                resp.set_cookie(
                    "session_token",  # Use SESSION_COOKIE_NAME from config
                    sess_token,
                    max_age=max_age,
                    httponly=True,
                    secure=current_app.config["SESSION_COOKIE_SECURE"],
                    samesite=current_app.config["SESSION_COOKIE_SAMESITE"],
                )
            return resp

        except (ValueError, KeyError, json.JSONDecodeError) as e:
            current_app.logger.error(f"Error processing Google OAuth response: {e}", exc_info=True)
            return redirect(url_for("login", error="google_oauth_failed"))

    except requests.RequestException as e:
        current_app.logger.error(f"Google OAuth request failed: {e}")
        return redirect(url_for("login", error="google_oauth_failed"))


# GitHub OAuth functions
def _github_oauth_state_make(next_url=""):
    """Generate a signed state token for GitHub OAuth."""
    return make_state_token(
        secret_key=config.SECRET_KEY, salt="github-oauth-state", next_url=next_url
    )


def _github_oauth_state_verify(state):
    """Verify the state token from GitHub OAuth."""
    return verify_state_token(secret_key=config.SECRET_KEY, salt="github-oauth-state", state=state)


def github_oauth_authorize():
    """Redirect to GitHub OAuth consent page."""
    if not config.GITHUB_OAUTH_ENABLED:
        current_app.logger.warning("GitHub OAuth not enabled")
        return redirect(url_for("login"))

    next_url = (request.args.get("next") or "").strip()
    if next_url and (not next_url.startswith("/") or "//" in next_url):
        next_url = ""

    state = _github_oauth_state_make(next_url)
    redirect_uri = urljoin(config.BASE_URL + "/", "auth/github/callback")

    params = {
        "client_id": config.GITHUB_CLIENT_ID,
        "redirect_uri": redirect_uri,
        "scope": "user:email",
        "state": state,
    }

    url = "https://github.com/login/oauth/authorize?" + urlencode(params)
    return redirect(url)


def github_oauth_callback():
    """Handle GitHub OAuth callback and authenticate user."""
    if not config.GITHUB_OAUTH_ENABLED:
        current_app.logger.warning("GitHub OAuth not enabled")
        return redirect(url_for("login"))

    code = request.args.get("code")
    state = request.args.get("state")
    payload = _github_oauth_state_verify(state)

    if not code or not payload:
        current_app.logger.warning("Missing code or state in GitHub OAuth callback")
        return redirect(url_for("login", error="github_oauth_failed"))

    redirect_uri = urljoin(config.BASE_URL + "/", "auth/github/callback")

    try:
        # Exchange authorization code for access token
        token_resp = requests.post(
            "https://github.com/login/oauth/access_token",
            data={
                "client_id": config.GITHUB_CLIENT_ID,
                "client_secret": config.GITHUB_CLIENT_SECRET,
                "code": code,
                "redirect_uri": redirect_uri,
            },
            headers={
                "Accept": "application/json",
                "Content-Type": "application/x-www-form-urlencoded",
            },
            timeout=15,
        )

        if token_resp.status_code != 200:
            current_app.logger.warning(f"GitHub token exchange failed: {token_resp.status_code}")
            return redirect(url_for("login", error="github_oauth_failed"))

        try:
            token_data = token_resp.json()
            access_token = token_data.get("access_token")
            if not access_token:
                raise ValueError("No access token in response")

            # Get user info
            user_resp = requests.get(
                "https://api.github.com/user",
                headers={
                    "Authorization": f"token {access_token}",
                    "Accept": "application/json",
                },
                timeout=10,
            )

            if user_resp.status_code != 200:
                current_app.logger.warning(f"GitHub userinfo failed: {user_resp.status_code}")
                return redirect(url_for("login", error="github_oauth_failed"))

            user_data = user_resp.json()

            # Get primary email if available
            email = None
            emails_resp = requests.get(
                "https://api.github.com/user/emails",
                headers={
                    "Authorization": f"token {access_token}",
                    "Accept": "application/json",
                },
                timeout=10,
            )

            if emails_resp.status_code == 200:
                emails = emails_resp.json()
                primary_email = next(
                    (e for e in emails if e.get("primary") and e.get("verified")), None
                )
                if primary_email:
                    email = primary_email.get("email", "").strip().lower()

            # Fallback to GitHub's public email if no primary/verified email found
            if not email and user_data.get("email"):
                email = user_data.get("email", "").strip().lower()

            if not email or "@" not in email:
                current_app.logger.warning("No valid email from GitHub OAuth")
                return redirect(url_for("login", error="github_email_required"))

            # Create/update user and log them in
            ensure_user_unverified(email, password=None)
            set_user_verified(email)

            # Create session
            sess_token, max_age = session_create(
                email, remember_me=True, user_agent=request.headers.get("User-Agent")
            )

            # Determine redirect URL
            next_url = (payload.get("next") or "").strip()
            if not next_url or not next_url.startswith("/") or "//" in next_url:
                next_url = url_for("index")

            # Set session cookie and redirect
            resp = redirect(next_url)
            if sess_token:
                resp.set_cookie(
                    "session_token",  # Use SESSION_COOKIE_NAME from config
                    sess_token,
                    max_age=max_age,
                    httponly=True,
                    secure=current_app.config["SESSION_COOKIE_SECURE"],
                    samesite=current_app.config["SESSION_COOKIE_SAMESITE"],
                )
            return resp

        except (ValueError, KeyError, json.JSONDecodeError) as e:
            current_app.logger.error(f"Error processing GitHub OAuth response: {e}", exc_info=True)
            return redirect(url_for("login", error="github_oauth_failed"))

    except requests.RequestException as e:
        current_app.logger.error(f"GitHub OAuth request failed: {e}")
        return redirect(url_for("login", error="github_oauth_failed"))
