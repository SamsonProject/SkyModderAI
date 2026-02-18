"""
OAuth state token management with database persistence.
Prevents CSRF attacks and handles server restarts during OAuth flow.
"""

import secrets
from datetime import datetime, timezone, timedelta
from typing import Optional, Tuple

from flask import current_app
from sqlalchemy import Column, DateTime, String
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class OAuthStateToken(Base):
    """Database model for storing OAuth state tokens with expiration."""

    __tablename__ = "oauth_state_tokens"

    token = Column(String(64), primary_key=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    provider = Column(String(32), nullable=False)  # 'google' or 'github'
    redirect_url = Column(String(512), nullable=True)

    @property
    def is_expired(self) -> bool:
        """Check if the token has expired (10 minutes)."""
        return (datetime.now(timezone.utc) - self.created_at) > timedelta(minutes=10)


def generate_state_token(provider: str, redirect_url: str = None) -> str:
    """
    Generate and store a new OAuth state token.

    Args:
        provider: OAuth provider name (e.g., 'google', 'github')
        redirect_url: Optional redirect URL to store with the token

    Returns:
        str: The generated state token
    """
    token = secrets.token_urlsafe(32)
    try:
        db = current_app.extensions["sqlalchemy"].db
        state_token = OAuthStateToken(token=token, provider=provider, redirect_url=redirect_url)
        db.session.add(state_token)
        db.session.commit()
        return token
    except SQLAlchemyError as e:
        current_app.logger.error(f"Failed to generate OAuth state token: {e}")
        db.session.rollback()
        raise


def verify_state_token(token: str, provider: str) -> Tuple[bool, Optional[str]]:
    """
    Verify and consume an OAuth state token.

    Args:
        token: The state token to verify
        provider: Expected OAuth provider

    Returns:
        Tuple[bool, Optional[str]]: (is_valid, redirect_url)
    """
    if not token:
        return False, None

    try:
        db = current_app.extensions["sqlalchemy"].db
        state_token = db.session.query(OAuthStateToken).get(token)

        if not state_token:
            current_app.logger.warning(f"Invalid OAuth state token: {token}")
            return False, None

        if state_token.provider != provider:
            current_app.logger.warning(
                f"OAuth state token provider mismatch: expected {provider}, got {state_token.provider}"
            )
            return False, None

        if state_token.is_expired:
            current_app.logger.warning(f"Expired OAuth state token: {token}")
            return False, None

        # Consume the token by deleting it
        db.session.delete(state_token)
        db.session.commit()

        return True, state_token.redirect_url

    except SQLAlchemyError as e:
        current_app.logger.error(f"Error verifying OAuth state token: {e}")
        return False, None


def cleanup_expired_tokens() -> int:
    """Remove expired OAuth state tokens from the database.

    Returns:
        int: Number of tokens deleted
    """
    try:
        db = current_app.extensions["sqlalchemy"].db
        expired = (
            db.session.query(OAuthStateToken)
            .filter(OAuthStateToken.created_at < (datetime.now(timezone.utc) - timedelta(minutes=10)))
            .delete()
        )
        db.session.commit()
        if expired:
            current_app.logger.info(f"Cleaned up {expired} expired OAuth state tokens")
        return expired
    except SQLAlchemyError as e:
        current_app.logger.error(f"Error cleaning up expired OAuth state tokens: {e}")
        db.session.rollback()
        return 0


def init_oauth_state_db(app):
    """Initialize the OAuth state token database."""
    with app.app_context():
        try:
            db = app.extensions["sqlalchemy"].db
            # Create tables if they don't exist
            Base.metadata.create_all(db.engine)
            # Clean up any expired tokens on startup
            cleanup_expired_tokens()
        except Exception as e:
            app.logger.error(f"Failed to initialize OAuth state database: {e}")
            raise
