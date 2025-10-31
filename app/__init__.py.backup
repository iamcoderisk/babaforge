"""
Enterprise Email System Application Factory
"""
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import redis
import logging
from logging.handlers import RotatingFileHandler
import os

db = SQLAlchemy()
migrate = Migrate()
limiter = Limiter(key_func=get_remote_address)
redis_client = None

def create_app(config_name='default'):
    """Application factory"""
    app = Flask(__name__)
    
    # Load configuration
    from app.config.settings import config
    app.config.from_object(config[config_name])
    
    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    CORS(app)
    limiter.init_app(app)
    
    # Initialize Redis
    global redis_client
    redis_client = redis.Redis(
        host=app.config['REDIS_HOST'],
        port=app.config['REDIS_PORT'],
        password=app.config.get('REDIS_PASSWORD'),
        db=app.config['REDIS_DB'],
        decode_responses=True
    )
    
    # Setup logging
    setup_logging(app)
    
    # Register blueprints
    register_blueprints(app)
    
    # Register error handlers
    register_error_handlers(app)
    
    # Shell context
    @app.shell_context_processor
    def make_shell_context():
        return {
            'db': db,
            'redis': redis_client
        }
    
    return app

def setup_logging(app):
    """Setup logging"""
    if not app.debug:
        if not os.path.exists('logs'):
            os.mkdir('logs')
        
        file_handler = RotatingFileHandler(
            'logs/email_system.log',
            maxBytes=10485760,
            backupCount=10
        )
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.INFO)
        app.logger.info('Enterprise Email System startup')

def register_blueprints(app):
    """Register all blueprints"""
    from app.controllers.main_controller import main_bp
    from app.controllers.api_controller import api_bp
    from app.controllers.dns_controller import dns_bp
    from app.controllers.dashboard_controller import dashboard_bp
    from app.controllers.email_controller import email_bp
    
    app.register_blueprint(main_bp)
    app.register_blueprint(api_bp, url_prefix='/api/v1')
    app.register_blueprint(dns_bp, url_prefix='/dns')
    app.register_blueprint(dashboard_bp, url_prefix='/dashboard')
    app.register_blueprint(email_bp, url_prefix='/emails')

def register_error_handlers(app):
    """Register error handlers"""
    @app.errorhandler(404)
    def not_found_error(error):
        return {'error': 'Not found'}, 404
    
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return {'error': 'Internal server error'}, 500
