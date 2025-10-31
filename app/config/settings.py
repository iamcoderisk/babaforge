"""
Application Configuration
"""
import os
from datetime import timedelta

class Config:
    """Base configuration"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # Database - Use SQLite for local development
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///email_system.db'
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_POOL_SIZE = int(os.environ.get('SQLALCHEMY_POOL_SIZE', 50))
    SQLALCHEMY_MAX_OVERFLOW = int(os.environ.get('SQLALCHEMY_MAX_OVERFLOW', 100))
    
    # Redis
    REDIS_HOST = os.environ.get('REDIS_HOST', 'localhost')
    REDIS_PORT = int(os.environ.get('REDIS_PORT', 6379))
    REDIS_PASSWORD = os.environ.get('REDIS_PASSWORD')
    REDIS_DB = int(os.environ.get('REDIS_DB', 0))
    REDIS_MAX_CONNECTIONS = int(os.environ.get('REDIS_MAX_CONNECTIONS', 1000))
    
    # Email System
    DOMAIN = os.environ.get('DOMAIN', 'sendbaba.com')
    DKIM_SELECTOR = os.environ.get('DKIM_SELECTOR', 'mail')
    DKIM_PRIVATE_KEY_PATH = 'data/dkim/private.key'
    DKIM_PUBLIC_KEY_PATH = 'data/dkim/public.key'
    
    # SMTP
    SMTP_POOL_SIZE = int(os.environ.get('SMTP_POOL_SIZE', 50))
    SMTP_TIMEOUT = int(os.environ.get('SMTP_TIMEOUT', 30))
    SMTP_MAX_RETRIES = int(os.environ.get('SMTP_MAX_RETRIES', 3))
    
    # Rate Limiting
    DEFAULT_RATE_LIMIT = int(os.environ.get('DEFAULT_RATE_LIMIT', 10000))
    GMAIL_RATE_LIMIT = int(os.environ.get('GMAIL_RATE_LIMIT', 3600))
    YAHOO_RATE_LIMIT = int(os.environ.get('YAHOO_RATE_LIMIT', 2000))
    OUTLOOK_RATE_LIMIT = int(os.environ.get('OUTLOOK_RATE_LIMIT', 5000))
    
    # Workers
    WORKER_CONCURRENCY = int(os.environ.get('WORKER_CONCURRENCY', 100))
    MIN_WORKERS = int(os.environ.get('MIN_WORKERS', 10))
    MAX_WORKERS = int(os.environ.get('MAX_WORKERS', 5000))
    
    # Targets
    TARGET_DAILY_VOLUME = int(os.environ.get('TARGET_DAILY_VOLUME', 2_000_000_000))
    TARGET_EMAILS_PER_SECOND = int(os.environ.get('TARGET_EMAILS_PER_SECOND', 23148))
    
    # IP Pool
    IP_POOL_ENABLED = os.environ.get('IP_POOL_ENABLED', 'true').lower() == 'true'
    IP_WARMUP_ENABLED = os.environ.get('IP_WARMUP_ENABLED', 'true').lower() == 'true'
    
    # Monitoring
    PROMETHEUS_ENABLED = os.environ.get('PROMETHEUS_ENABLED', 'true').lower() == 'true'
    PROMETHEUS_PORT = int(os.environ.get('PROMETHEUS_PORT', 9090))

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    TESTING = False

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    TESTING = False
    # For production, use PostgreSQL
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        f"postgresql://{os.environ.get('POSTGRES_USER', 'emailer')}:" \
        f"{os.environ.get('POSTGRES_PASSWORD', 'password')}@" \
        f"{os.environ.get('POSTGRES_HOST', 'localhost')}:" \
        f"{os.environ.get('POSTGRES_PORT', '5432')}/" \
        f"{os.environ.get('POSTGRES_DB', 'email_system')}"

class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
