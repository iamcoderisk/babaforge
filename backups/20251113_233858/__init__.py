from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
import os
import logging

# Initialize extensions
db = SQLAlchemy()
login_manager = LoginManager()
migrate = Migrate()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Redis client
try:
    import redis
    redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
    redis_client.ping()
    logger.info("✅ Redis connected")
except Exception as e:
    redis_client = None
    logger.warning(f"⚠️  Redis not available: {e}")

def create_app():
    app = Flask(__name__)
    
    # Configuration
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', '60b55ca25a3391f98774c37d68c65b88')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'postgresql://emailer:SecurePassword123@localhost:5432/emailer')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    login_manager.login_view = 'auth.login'
    
    with app.app_context():
        # Import and register blueprints
        try:
            from app.controllers.main_controller import main_bp
            app.register_blueprint(main_bp)
            logger.info("✅ Main")
        except Exception as e:
            logger.error(f"❌ Main: {e}")
        
        try:
            from app.controllers.auth_controller import auth_bp
            app.register_blueprint(auth_bp)
            logger.info("✅ Auth")
        except Exception as e:
            logger.error(f"❌ Auth: {e}")
        
        try:
            from app.controllers.dashboard_controller import dashboard_bp
            app.register_blueprint(dashboard_bp)
            logger.info("✅ Dashboard")
        except Exception as e:
            logger.error(f"❌ Dashboard: {e}")
        
        try:
            from app.controllers.api_controller import api_bp
            app.register_blueprint(api_bp)
            logger.info("✅ API")
        except Exception as e:
            logger.error(f"❌ API: {e}")
        
        try:
            from app.controllers.campaign_controller import campaign_bp
            app.register_blueprint(campaign_bp)
            logger.info("✅ Campaigns")
        except Exception as e:
            logger.error(f"❌ Campaigns: {e}")
        
        try:
            from app.controllers.contact_controller import contact_bp
            app.register_blueprint(contact_bp)
            logger.info("✅ Contacts")
        except Exception as e:
            logger.error(f"❌ Contacts: {e}")
        
        try:
            from app.controllers.domain_controller import domain_bp
            app.register_blueprint(domain_bp)
            logger.info("✅ Domains")
        except Exception as e:
            logger.error(f"❌ Domains: {e}")
        
        try:
            from app.controllers.settings_controller import settings_bp
            app.register_blueprint(settings_bp)
            logger.info("✅ Settings")
        except Exception as e:
            logger.error(f"❌ Settings: {e}")
        
        try:
            from app.controllers.analytics_controller import analytics_bp
            app.register_blueprint(analytics_bp)
            logger.info("✅ Analytics")
        except Exception as e:
            logger.error(f"❌ Analytics: {e}")
        
        try:
            from app.controllers.segment_controller import segment_bp
            app.register_blueprint(segment_bp)
            logger.info("✅ Segments")
        except Exception as e:
            logger.error(f"❌ Segments: {e}")
        
        try:
            from app.controllers.workflow_controller import workflow_bp
            app.register_blueprint(workflow_bp)
            logger.info("✅ Workflows")
        except Exception as e:
            logger.error(f"❌ Workflows: {e}")
        
        try:
            from app.controllers.form_controller import form_bp
            app.register_blueprint(form_bp)
            logger.info("✅ Forms")
        except Exception as e:
            logger.error(f"❌ Forms: {e}")
        
        try:
            from app.controllers.template_controller import template_bp
            app.register_blueprint(template_bp)
            logger.info("✅ Templates")
        except Exception as e:
            logger.error(f"❌ Templates: {e}")
        
        try:
            from app.controllers.validation_controller import validation_bp
            app.register_blueprint(validation_bp)
            logger.info("✅ Validation")
        except Exception as e:
            logger.error(f"❌ Validation: {e}")
        
        try:
            from app.controllers.warmup_controller import warmup_bp
            app.register_blueprint(warmup_bp)
            logger.info("✅ Warmup")
        except Exception as e:
            logger.error(f"❌ Warmup: {e}")
        
        try:
            from app.controllers.integration_controller import integration_bp
            app.register_blueprint(integration_bp)
            logger.info("✅ Integrations")
        except Exception as e:
            logger.error(f"❌ Integrations: {e}")
        
        try:
            from app.controllers.reply_controller import reply_bp
            app.register_blueprint(reply_bp)
            logger.info("✅ Reply AI")
        except Exception as e:
            logger.error(f"❌ Reply AI: {e}")
    
    @login_manager.user_loader
    def load_user(user_id):
        from app.models.user import User
        try:
            return User.query.get(user_id)
        except:
            try:
                return User.query.get(int(user_id))
            except:
                return None
    
    # Template API route
    @app.route('/api/templates/<template_name>')
    def serve_template(template_name):
        """Serve email templates"""
        import os
        try:
            template_path = os.path.join('app', 'templates', 'email_templates', f'{template_name}.html')
            if os.path.exists(template_path):
                with open(template_path, 'r') as f:
                    return f.read(), 200, {'Content-Type': 'text/html; charset=utf-8'}
            return 'Template not found', 404
        except Exception as e:
            return str(e), 500
    

    return app
