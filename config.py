"""
API Gateway — Configuration module.
"""
import os


class Config:
    """Base configuration."""
    SECRET_KEY = os.environ.get('JWT_SECRET', 'dev-secret-key')
    JWT_ALGORITHM = os.environ.get('JWT_ALGORITHM', 'HS256')
    JWT_EXPIRY_HOURS = int(os.environ.get('JWT_EXPIRY_HOURS', 24))

    # Service URLs
    PORTFOLIO_SERVICE_URL = os.environ.get('PORTFOLIO_SERVICE_URL', 'http://localhost:5001')
    NOTIFICATION_SERVICE_URL = os.environ.get('NOTIFICATION_SERVICE_URL', 'http://localhost:5002')

    # Redis (rate limiting)
    REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')

    # Rate limiting
    RATE_LIMIT_DEFAULT = os.environ.get('RATE_LIMIT_DEFAULT', '100/hour')

    # Logging
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False


class TestingConfig(Config):
    TESTING = True


config_map = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
}
