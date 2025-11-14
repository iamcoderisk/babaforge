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