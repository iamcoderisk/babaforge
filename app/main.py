
# ============= app/main.py =============
"""
Main Flask Application
"""
from flask import Flask
from flask_cors import CORS
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session

from app.config.settings import settings
from app.models.database import Base
from app.utils.logger import setup_logging, get_logger
from app.controllers import email_controller, organization_controller, domain_controller, analytics_controller

logger = get_logger(__name__)

def create_app() -> Flask:
    """Application factory"""
    
    # Setup logging
    setup_logging()
    
    # Create Flask app
    app = Flask(__name__)
    app.config['SECRET_KEY'] = settings.SECRET_KEY
    app.config['JSON_SORT_KEYS'] = False
    
    # Enable CORS
    CORS(app)
    
    # Database setup
    engine = create_engine(
        settings.DATABASE_URL,
        pool_size=settings.DB_POOL_MAX,
        max_overflow=settings.DB_MAX_OVERFLOW,
        pool_timeout=settings.DB_POOL_TIMEOUT,
        pool_pre_ping=True,
        echo=settings.DEBUG
    )
    
    # Create tables
    Base.metadata.create_all(engine)
    
    # Session factory
    session_factory = sessionmaker(bind=engine)
    Session = scoped_session(session_factory)
    
    # Store session in app context
    app.session = Session
    
    # Register blueprints
    app.register_blueprint(email_controller.bp, url_prefix='/api/v1/emails')
    app.register_blueprint(organization_controller.bp, url_prefix='/api/v1/organizations')
    app.register_blueprint(domain_controller.bp, url_prefix='/api/v1/domains')
    app.register_blueprint(analytics_controller.bp, url_prefix='/api/v1/analytics')
    
    # Health check
    @app.route('/health')
    def health_check():
        return {
            'status': 'healthy',
            'version': settings.APP_VERSION,
            'environment': settings.ENVIRONMENT
        }
    
    # Teardown
    @app.teardown_appcontext
    def shutdown_session(exception=None):
        Session.remove()
    
    logger.info(f"Application initialized: {settings.APP_NAME} v{settings.APP_VERSION}")
    
    return app
