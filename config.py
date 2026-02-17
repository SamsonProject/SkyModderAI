"""
Centralized configuration management for SkyModderAI.
Loads settings from environment variables with sensible defaults for development.
"""
import logging
import os
from pathlib import Path

try:
    from dotenv import load_dotenv
except ModuleNotFoundError:  # pragma: no cover
    def load_dotenv(*args, **kwargs):  # type: ignore[no-redef]
        logging.getLogger(__name__).warning(
            "python-dotenv is not installed; skipping .env loading. "
            "Install it with: pip install -r requirements.txt"
        )

# Load environment variables from .env file if it exists
env_path = Path('.') / '.env'
load_dotenv(dotenv_path=env_path)

class Config:
    # Application
    FLASK_ENV = os.getenv('FLASK_ENV', 'development')
    DEBUG = FLASK_ENV != 'production'
    SECRET_KEY = os.getenv('SECRET_KEY', os.urandom(32).hex())
    BASE_URL = os.getenv('BASE_URL', 'http://localhost:5000').rstrip('/')

    # Database
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///instance/app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Email (SendGrid)
    MAIL_SERVER = os.getenv('MAIL_SERVER', 'smtp.sendgrid.net')
    MAIL_PORT = int(os.getenv('MAIL_PORT', 587))
    MAIL_USE_TLS = os.getenv('MAIL_USE_TLS', '1') == '1'
    MAIL_USERNAME = os.getenv('MAIL_USERNAME', 'apikey')
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.getenv('MAIL_DEFAULT_SENDER', 'noreply@skymodderai.com')

    # OAuth - Google
    GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID')
    GOOGLE_CLIENT_SECRET = os.getenv('GOOGLE_CLIENT_SECRET')
    GOOGLE_OAUTH_ENABLED = bool(GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET)

    # OAuth - GitHub
    GITHUB_CLIENT_ID = os.getenv('GITHUB_CLIENT_ID')
    GITHUB_CLIENT_SECRET = os.getenv('GITHUB_CLIENT_SECRET')
    GITHUB_OAUTH_ENABLED = bool(GITHUB_CLIENT_ID and GITHUB_CLIENT_SECRET)

    # Stripe
    STRIPE_PUBLISHABLE_KEY = os.getenv('STRIPE_PUBLISHABLE_KEY')
    STRIPE_SECRET_KEY = os.getenv('STRIPE_SECRET_KEY')
    STRIPE_WEBHOOK_SECRET = os.getenv('STRIPE_WEBHOOK_SECRET')
    STRIPE_PRO_PRICE_ID = os.getenv('STRIPE_PRO_PRICE_ID')
    STRIPE_OPENCLAW_PRICE_ID = os.getenv('STRIPE_OPENCLAW_PRICE_ID')
    PAYMENTS_ENABLED = bool(STRIPE_SECRET_KEY and STRIPE_SECRET_KEY.startswith('sk_'))

    # Rate Limiting
    RATE_LIMIT_DEFAULT = os.getenv('RATE_LIMIT_DEFAULT', '100/1minute')
    RATE_LIMIT_AUTH = os.getenv('RATE_LIMIT_AUTH', '10/1minute')
    RATE_LIMIT_API = os.getenv('RATE_LIMIT_API', '60/1minute')

    # Security Headers
    SESSION_COOKIE_SECURE = os.getenv('SESSION_COOKIE_SECURE', str(FLASK_ENV == 'production')).lower() == 'true'
    SESSION_COOKIE_HTTPONLY = os.getenv('SESSION_COOKIE_HTTPONLY', 'True').lower() == 'true'
    SESSION_COOKIE_SAMESITE = os.getenv('SESSION_COOKIE_SAMESITE', 'Lax')

    # Feature Flags
    MODCHECK_OPENCLAW_ENABLED = os.getenv('MODCHECK_OPENCLAW_ENABLED', '0') == '1'
    MODCHECK_DEV_PRO = os.getenv('MODCHECK_DEV_PRO', '0') == '1' if FLASK_ENV != 'production' else False
    MODCHECK_TEST_PRO_EMAIL = os.getenv('MODCHECK_TEST_PRO_EMAIL') if FLASK_ENV != 'production' else None

    # OpenAI
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    AI_CHAT_ENABLED = bool(OPENAI_API_KEY)

    @classmethod
    def validate_config(cls):
        """Validate required configuration and log warnings for missing or invalid settings."""
        logger = logging.getLogger(__name__)

        # Check required production settings
        if cls.FLASK_ENV == 'production':
            if not cls.SECRET_KEY or len(cls.SECRET_KEY) < 32:
                logger.error('SECRET_KEY is too short (min 32 chars) or not set in production!')

            if not all([cls.MAIL_SERVER, cls.MAIL_USERNAME, cls.MAIL_PASSWORD]):
                logger.warning('Email configuration is incomplete. Email features will be disabled.')

            if not all([cls.STRIPE_PUBLISHABLE_KEY, cls.STRIPE_SECRET_KEY, cls.STRIPE_PRO_PRICE_ID]):
                logger.warning('Stripe configuration is incomplete. Payment features will be disabled.')

            if not all([cls.GOOGLE_CLIENT_ID, cls.GOOGLE_CLIENT_SECRET]):
                logger.warning('Google OAuth configuration is incomplete. Google login will be disabled.')

            if not all([cls.GITHUB_CLIENT_ID, cls.GITHUB_CLIENT_SECRET]):
                logger.warning('GitHub OAuth configuration is incomplete. GitHub login will be disabled.')

# Initialize configuration
config = Config()
config.validate_config()

# Log configuration status
logger = logging.getLogger(__name__)
logger.info(f"Running in {config.FLASK_ENV} mode")
if config.PAYMENTS_ENABLED:
    logger.info("Payments enabled")
else:
    logger.warning("Payments disabled - check Stripe configuration")

if config.AI_CHAT_ENABLED:
    logger.info("AI chat enabled")
else:
    logger.warning("AI chat disabled - OPENAI_API_KEY not set")
