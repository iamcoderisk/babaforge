
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


# ============= app/controllers/email_controller.py =============
"""
Email Controller - API endpoints for email operations
"""
from flask import Blueprint, request, jsonify, current_app
from pydantic import ValidationError

from app.models.schemas import EmailSendRequest, EmailBatchRequest
from app.services.email_service import EmailService
from app.middleware.auth import require_api_key
from app.utils.logger import get_logger

logger = get_logger(__name__)
bp = Blueprint('emails', __name__)

@bp.route('/send', methods=['POST'])
@require_api_key
def send_email(org_id: int):
    """Send single email"""
    try:
        # Validate request
        email_request = EmailSendRequest(**request.json)
        
        # Get database session
        db = current_app.session()
        
        # Send email
        email_service = EmailService(db)
        import asyncio
        email = asyncio.run(email_service.send_email(org_id, email_request))
        
        return jsonify({
            'success': True,
            'message_id': email.message_id,
            'status': email.status,
            'queued_at': email.created_at.isoformat()
        }), 202
        
    except ValidationError as e:
        return jsonify({'error': 'Validation error', 'details': e.errors()}), 400
    except Exception as e:
        logger.error(f"Error sending email: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/send/batch', methods=['POST'])
@require_api_key
def send_batch(org_id: int):
    """Send batch of emails"""
    try:
        # Validate request
        batch_request = EmailBatchRequest(**request.json)
        
        # Get database session
        db = current_app.session()
        
        # Send batch
        email_service = EmailService(db)
        import asyncio
        emails = asyncio.run(email_service.send_batch(org_id, batch_request.emails))
        
        return jsonify({
            'success': True,
            'count': len(emails),
            'message_ids': [e.message_id for e in emails]
        }), 202
        
    except Exception as e:
        logger.error(f"Error sending batch: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/<message_id>', methods=['GET'])
@require_api_key
def get_email(org_id: int, message_id: str):
    """Get email details"""
    try:
        db = current_app.session()
        from app.models.database import EmailOutgoing
        
        email = db.query(EmailOutgoing).filter_by(
            org_id=org_id,
            message_id=message_id
        ).first()
        
        if not email:
            return jsonify({'error': 'Email not found'}), 404
        
        return jsonify({
            'message_id': email.message_id,
            'status': email.status,
            'sender': email.sender,
            'recipients': email.recipients,
            'subject': email.subject,
            'created_at': email.created_at.isoformat(),
            'delivered_at': email.delivered_at.isoformat() if email.delivered_at else None,
            'opened': email.opened,
            'clicked': email.clicked,
            'tags': email.tags
        })
        
    except Exception as e:
        logger.error(f"Error getting email: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/track/open/<message_id>', methods=['GET'])
def track_open(message_id: str):
    """Track email open"""
    try:
        db = current_app.session()
        from app.models.database import EmailOutgoing
        from datetime import datetime
        
        email = db.query(EmailOutgoing).filter_by(message_id=message_id).first()
        
        if email and not email.opened:
            email.opened = True
            email.opened_at = datetime.utcnow()
            email.open_count += 1
            db.commit()
        
        # Return 1x1 transparent GIF
        from flask import make_response
        response = make_response(
            b'\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x80\x00\x00\xff\xff\xff\x00\x00\x00\x21\xf9\x04\x01\x00\x00\x00\x00\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02\x44\x01\x00\x3b'
        )
        response.headers['Content-Type'] = 'image/gif'
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        return response
        
    except Exception as e:
        logger.error(f"Error tracking open: {e}")
        return '', 404


# ============= app/controllers/organization_controller.py =============
"""
Organization Controller
"""
from flask import Blueprint, request, jsonify, current_app
import secrets

from app.models.database import Organization
from app.models.schemas import OrganizationCreate
from app.middleware.auth import require_admin
from app.utils.logger import get_logger

logger = get_logger(__name__)
bp = Blueprint('organizations', __name__)

@bp.route('/', methods=['POST'])
@require_admin
def create_organization():
    """Create new organization"""
    try:
        org_data = OrganizationCreate(**request.json)
        
        db = current_app.session()
        
        # Generate API key
        api_key = secrets.token_urlsafe(32)
        
        # Create organization
        org = Organization(
            name=org_data.name,
            api_key=api_key,
            max_emails_per_hour=org_data.max_emails_per_hour
        )
        
        db.add(org)
        db.commit()
        db.refresh(org)
        
        return jsonify({
            'id': org.id,
            'uuid': str(org.uuid),
            'name': org.name,
            'api_key': api_key,
            'created_at': org.created_at.isoformat()
        }), 201
        
    except Exception as e:
        logger.error(f"Error creating organization: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/<int:org_id>', methods=['GET'])
@require_admin
def get_organization(org_id: int):
    """Get organization details"""
    try:
        db = current_app.session()
        org = db.query(Organization).filter_by(id=org_id).first()
        
        if not org:
            return jsonify({'error': 'Organization not found'}), 404
        
        return jsonify({
            'id': org.id,
            'name': org.name,
            'status': org.status,
            'max_emails_per_hour': org.max_emails_per_hour,
            'created_at': org.created_at.isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error getting organization: {e}")
        return jsonify({'error': str(e)}), 500


# ============= app/controllers/domain_controller.py =============
"""
Domain Controller
"""
from flask import Blueprint, request, jsonify, current_app

from app.models.database import Domain
from app.models.schemas import DomainCreate
from app.services.dkim_service import DKIMService
from app.middleware.auth import require_api_key
from app.utils.logger import get_logger

logger = get_logger(__name__)
bp = Blueprint('domains', __name__)

@bp.route('/', methods=['POST'])
@require_api_key
def create_domain(org_id: int):
    """Create new domain"""
    try:
        domain_data = DomainCreate(**request.json)
        
        db = current_app.session()
        
        # Get DKIM records
        dkim_service = DKIMService()
        dkim_record = dkim_service.get_dns_record()
        
        # Create domain
        domain = Domain(
            org_id=org_id,
            domain=domain_data.domain,
            dkim_selector='default',
            dkim_public_key=dkim_record,
            spf_record=f"v=spf1 mx a:{domain_data.domain} ~all",
            dmarc_record=f"v=DMARC1; p=quarantine; rua=mailto:dmarc@{domain_data.domain}",
            status='pending'
        )
        
        db.add(domain)
        db.commit()
        db.refresh(domain)
        
        return jsonify({
            'id': domain.id,
            'domain': domain.domain,
            'dns_records': {
                'dkim': {
                    'name': f'{domain.dkim_selector}._domainkey.{domain.domain}',
                    'type': 'TXT',
                    'value': domain.dkim_public_key
                },
                'spf': {
                    'name': domain.domain,
                    'type': 'TXT',
                    'value': domain.spf_record
                },
                'dmarc': {
                    'name': f'_dmarc.{domain.domain}',
                    'type': 'TXT',
                    'value': domain.dmarc_record
                }
            }
        }), 201
        
    except Exception as e:
        logger.error(f"Error creating domain: {e}")
        return jsonify({'error': str(e)}), 500