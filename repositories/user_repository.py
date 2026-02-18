"""
SkyModderAI - User Repository

Database access layer for user-related operations.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from exceptions import DatabaseOperationError, UserNotFoundError
from models import APIKey, User, UserSession

logger = logging.getLogger(__name__)


class UserRepository:
    """Repository for user database operations."""

    def __init__(self, session: Session) -> None:
        """
        Initialize user repository.

        Args:
            session: SQLAlchemy session
        """
        self.session = session

    def get_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """
        Get user by email.

        Args:
            email: User email

        Returns:
            User data as dict or None
        """
        try:
            user = self.session.query(User).filter(User.email == email).first()
            if user:
                return {
                    "email": user.email,
                    "tier": user.tier,
                    "customer_id": user.customer_id,
                    "subscription_id": user.subscription_id,
                    "email_verified": user.email_verified,
                    "password_hash": user.password_hash,
                    "created_at": user.created_at,
                    "last_updated": user.last_updated,
                }
            return None
        except Exception as e:
            logger.error(f"Failed to get user by email: {e}")
            raise DatabaseOperationError(str(e))

    def create(
        self,
        email: str,
        password_hash: Optional[str] = None,
        email_verified: bool = False,
    ) -> Dict[str, Any]:
        """
        Create new user.

        Args:
            email: User email
            password_hash: Hashed password
            email_verified: Email verification status

        Returns:
            Created user data

        Raises:
            DatabaseOperationError: If creation fails
        """
        try:
            user = User(
                email=email,
                password_hash=password_hash,
                email_verified=email_verified,
                created_at=datetime.now(timezone.utc),
                last_updated=datetime.now(timezone.utc),
            )
            self.session.add(user)
            self.session.commit()
            self.session.refresh(user)

            logger.info(f"User created: {email}")

            return {
                "email": user.email,
                "tier": user.tier,
                "email_verified": user.email_verified,
                "created_at": user.created_at,
            }
        except Exception as e:
            self.session.rollback()
            logger.error(f"Failed to create user: {e}")
            raise DatabaseOperationError(str(e))

    def update(self, email: str, **kwargs: Any) -> Optional[Dict[str, Any]]:
        """
        Update user fields.

        Args:
            email: User email
            **kwargs: Fields to update

        Returns:
            Updated user data or None
        """
        try:
            user = self.session.query(User).filter(User.email == email).first()
            if not user:
                return None

            # Update allowed fields
            allowed_fields = {
                "tier",
                "customer_id",
                "subscription_id",
                "email_verified",
                "password_hash",
            }

            for key, value in kwargs.items():
                if key in allowed_fields:
                    setattr(user, key, value)

            user.last_updated = datetime.now(timezone.utc)
            self.session.commit()
            self.session.refresh(user)

            logger.info(f"User updated: {email}")

            return {
                "email": user.email,
                "tier": user.tier,
                "email_verified": user.email_verified,
            }
        except Exception as e:
            self.session.rollback()
            logger.error(f"Failed to update user: {e}")
            raise DatabaseOperationError(str(e))

    def delete(self, email: str) -> bool:
        """
        Delete user.

        Args:
            email: User email

        Returns:
            True if deleted
        """
        try:
            user = self.session.query(User).filter(User.email == email).first()
            if not user:
                return False

            self.session.delete(user)
            self.session.commit()

            logger.info(f"User deleted: {email}")
            return True
        except Exception as e:
            self.session.rollback()
            logger.error(f"Failed to delete user: {e}")
            raise DatabaseOperationError(str(e))

    def create_session(
        self,
        email: str,
        token: str,
        display_id: str,
        user_agent: str,
        expires_at: int,
    ) -> Dict[str, Any]:
        """
        Create user session.

        Args:
            email: User email
            token: Session token
            display_id: Display ID for device
            user_agent: User agent string
            expires_at: Expiration timestamp

        Returns:
            Created session data
        """
        try:
            user_session = UserSession(
                token=token,
                display_id=display_id,
                user_email=email,
                user_agent=user_agent,
                created_at=datetime.now(timezone.utc),
                last_seen=datetime.now(timezone.utc),
                expires_at=expires_at,
            )
            self.session.add(user_session)
            self.session.commit()

            logger.info(f"Session created for user: {email}")

            return {
                "token": user_session.token,
                "display_id": user_session.display_id,
                "created_at": user_session.created_at,
                "expires_at": user_session.expires_at,
            }
        except Exception as e:
            self.session.rollback()
            logger.error(f"Failed to create session: {e}")
            raise DatabaseOperationError(str(e))

    def get_session(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Get session by token.

        Args:
            token: Session token

        Returns:
            Session data or None
        """
        try:
            user_session = self.session.query(UserSession).filter(
                UserSession.token == token
            ).first()

            if user_session:
                return {
                    "token": user_session.token,
                    "display_id": user_session.display_id,
                    "user_email": user_session.user_email,
                    "user_agent": user_session.user_agent,
                    "created_at": user_session.created_at,
                    "last_seen": user_session.last_seen,
                    "expires_at": user_session.expires_at,
                }
            return None
        except Exception as e:
            logger.error(f"Failed to get session: {e}")
            raise DatabaseOperationError(str(e))

    def delete_session(self, token: str) -> bool:
        """
        Delete session.

        Args:
            token: Session token

        Returns:
            True if deleted
        """
        try:
            user_session = self.session.query(UserSession).filter(
                UserSession.token == token
            ).first()

            if user_session:
                self.session.delete(user_session)
                self.session.commit()
                return True

            return False
        except Exception as e:
            self.session.rollback()
            logger.error(f"Failed to delete session: {e}")
            raise DatabaseOperationError(str(e))

    def get_sessions(self, email: str) -> List[Dict[str, Any]]:
        """
        Get all sessions for user.

        Args:
            email: User email

        Returns:
            List of session data
        """
        try:
            sessions = self.session.query(UserSession).filter(
                UserSession.user_email == email
            ).all()

            return [
                {
                    "token": s.token,
                    "display_id": s.display_id,
                    "created_at": s.created_at,
                    "last_seen": s.last_seen,
                    "expires_at": s.expires_at,
                }
                for s in sessions
            ]
        except Exception as e:
            logger.error(f"Failed to get user sessions: {e}")
            raise DatabaseOperationError(str(e))

    def create_api_key(
        self,
        email: str,
        key_hash: str,
        key_prefix: str,
        label: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Create API key.

        Args:
            email: User email
            key_hash: Hashed API key
            key_prefix: Key prefix for display
            label: Optional label

        Returns:
            Created API key data
        """
        try:
            api_key = APIKey(
                user_email=email,
                key_hash=key_hash,
                key_prefix=key_prefix,
                label=label,
                created_at=datetime.now(timezone.utc),
            )
            self.session.add(api_key)
            self.session.commit()
            self.session.refresh(api_key)

            logger.info(f"API key created for user: {email}")

            return {
                "id": api_key.id,
                "key_prefix": api_key.key_prefix,
                "label": api_key.label,
                "created_at": api_key.created_at,
            }
        except Exception as e:
            self.session.rollback()
            logger.error(f"Failed to create API key: {e}")
            raise DatabaseOperationError(str(e))

    def get_api_key(self, key_hash: str) -> Optional[Dict[str, Any]]:
        """
        Get API key by hash.

        Args:
            key_hash: Hashed API key

        Returns:
            API key data or None
        """
        try:
            api_key = self.session.query(APIKey).filter(
                APIKey.key_hash == key_hash
            ).first()

            if api_key:
                return {
                    "id": api_key.id,
                    "user_email": api_key.user_email,
                    "key_prefix": api_key.key_prefix,
                    "label": api_key.label,
                    "created_at": api_key.created_at,
                }
            return None
        except Exception as e:
            logger.error(f"Failed to get API key: {e}")
            raise DatabaseOperationError(str(e))

    def get_api_keys(self, email: str) -> List[Dict[str, Any]]:
        """
        Get all API keys for user.

        Args:
            email: User email

        Returns:
            List of API key data
        """
        try:
            api_keys = self.session.query(APIKey).filter(
                APIKey.user_email == email
            ).all()

            return [
                {
                    "id": key.id,
                    "key_prefix": key.key_prefix,
                    "label": key.label,
                    "created_at": key.created_at,
                }
                for key in api_keys
            ]
        except Exception as e:
            logger.error(f"Failed to get API keys: {e}")
            raise DatabaseOperationError(str(e))

    def delete_api_key(self, email: str, key_id: int) -> bool:
        """
        Delete API key.

        Args:
            email: User email
            key_id: API key ID

        Returns:
            True if deleted
        """
        try:
            api_key = self.session.query(APIKey).filter(
                APIKey.id == key_id,
                APIKey.user_email == email,
            ).first()

            if api_key:
                self.session.delete(api_key)
                self.session.commit()
                return True

            return False
        except Exception as e:
            self.session.rollback()
            logger.error(f"Failed to delete API key: {e}")
            raise DatabaseOperationError(str(e))
