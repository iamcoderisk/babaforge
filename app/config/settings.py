import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Base configuration"""
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    
    # Force PostgreSQL
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 
        'postgresql://emailer:SecurePassword123@localhost:5432/emailer')
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
    }
    
    # Redis
    REDIS_HOST = os.environ.get('REDIS_HOST', 'localhost')
    REDIS_PORT = int(os.environ.get('REDIS_PORT', 6379))
    REDIS_PASSWORD = os.environ.get('REDIS_PASSWORD')
    REDIS_DB = int(os.environ.get('REDIS_DB', 0))
    
    # Email Configuration
    DOMAIN = os.environ.get('DOMAIN', 'sendbaba.com')
    SERVER_IP = os.environ.get('SERVER_IP', '156.67.29.186')
    
    # SMTP Settings
    SMTP_MAX_RETRIES = int(os.environ.get('SMTP_MAX_RETRIES', 3))
    SMTP_TIMEOUT = int(os.environ.get('SMTP_TIMEOUT', 60))
    
    # Workers
    WORKER_CONCURRENCY = int(os.environ.get('WORKER_CONCURRENCY', 100))
    MIN_WORKERS = int(os.environ.get('MIN_WORKERS', 10))
    MAX_WORKERS = int(os.environ.get('MAX_WORKERS', 500))

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    TESTING = False

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    TESTING = False

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': ProductionConfig
}
