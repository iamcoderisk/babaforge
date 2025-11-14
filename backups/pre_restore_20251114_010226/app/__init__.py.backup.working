from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
import os

db = SQLAlchemy()
login_manager = LoginManager()
migrate = Migrate()

try:
    import redis
    redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
    redis_client.ping()
except:
    redis_client = None

def create_app():
    app = Flask(__name__)
    
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', '60b55ca25a3391f98774c37d68c65b88')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'postgresql://emailer:SecurePassword123@localhost:5432/emailer')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    login_manager.login_view = 'auth.login'
    
    with app.app_context():
        # Core controllers
        from app.controllers.main_controller import main_bp
        from app.controllers.auth_controller import auth_bp
        from app.controllers.dashboard_controller import dashboard_bp
        from app.controllers.api_controller import api_bp
        
        # OLD working controllers (campaigns, contacts, domains)
        from app.controllers.campaign_controller import campaign_bp
        from app.controllers.contact_controller import contact_bp
        from app.controllers.domain_controller import domain_bp
        
        # Settings
        from app.controllers.settings_controller import settings_bp
        from app.controllers.analytics_controller import analytics_bp
        
        # NEW feature controllers
        from app.controllers.segment_controller import segment_bp
        from app.controllers.workflow_controller import workflow_bp
        from app.controllers.form_controller import form_bp
        from app.controllers.template_controller import template_bp
        from app.controllers.validation_controller import validation_bp
        from app.controllers.warmup_controller import warmup_bp
        from app.controllers.integration_controller import integration_bp
        from app.controllers.reply_controller import reply_bp
        
        # Register all blueprints
        app.register_blueprint(main_bp)
        app.register_blueprint(auth_bp)
        app.register_blueprint(dashboard_bp)
        app.register_blueprint(api_bp)
        app.register_blueprint(campaign_bp)
        app.register_blueprint(contact_bp)
        app.register_blueprint(domain_bp)
        app.register_blueprint(settings_bp)
        app.register_blueprint(analytics_bp)
        app.register_blueprint(segment_bp)
        app.register_blueprint(workflow_bp)
        app.register_blueprint(form_bp)
        app.register_blueprint(template_bp)
        app.register_blueprint(validation_bp)
        app.register_blueprint(warmup_bp)
        app.register_blueprint(integration_bp)
        app.register_blueprint(reply_bp)
    
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
    
    return app
