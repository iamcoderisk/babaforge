from flask import Blueprint, request, jsonify, g
from app.middleware.legacy_api_auth import require_api_key_legacy
from app.middleware.rate_limiter import rate_limit_decorator
from app import db, redis_client
from app.models.email import Email
from app.models.contact import Contact
from app.models.campaign import Campaign
from app.models.organization import Organization
from datetime import datetime
import uuid
import json
import logging

logger = logging.getLogger(__name__)

# Create API v1 Blueprint
api_v1_bp = Blueprint('api_v1', __name__, url_prefix='/api/v1')


# ============================================
# EMAILS API
# ============================================

@api_v1_bp.route('/emails/send', methods=['POST'])
@require_api_key_legacy(['emails.send'])
@rate_limit_decorator
def send_email():
    """
    Send a single email
    
    POST /api/v1/emails/send
    """
    try:
        data = request.json
        
        # Validate required fields
        if not data.get('to'):
            return jsonify({
                'error': 'validation_error',
                'message': 'Recipient email (to) is required'
            }), 400
        
        if not data.get('subject'):
            return jsonify({
                'error': 'validation_error',
                'message': 'Subject is required'
            }), 400
        
        if not data.get('html') and not data.get('text'):
            return jsonify({
                'error': 'validation_error',
                'message': 'Either html or text body is required'
            }), 400
        
        # Create email record
        email_id = str(uuid.uuid4())
        from_email = data.get('from', 'noreply@sendbaba.com')
        to_email = data.get('to')
        
        # Create email with ONLY fields that exist in database
        email = Email(
            id=email_id,
            organization_id=g.organization_id,
            sender=from_email,
            recipient=to_email,
            from_email=from_email,
            to_email=to_email,
            subject=data.get('subject'),
            html_body=data.get('html', ''),
            text_body=data.get('text', ''),
            status='queued',
            created_at=datetime.utcnow()
        )
        
        db.session.add(email)
        db.session.commit()
        
        # Queue for sending
        email_data = {
            'id': email_id,
            'from': from_email,
            'to': to_email,
            'subject': data.get('subject'),
            'html_body': data.get('html', ''),
            'text_body': data.get('text', ''),
            'priority': data.get('priority', 5),
            'tags': data.get('tags', [])
        }
        
        priority = data.get('priority', 5)
        redis_client.lpush(f'outgoing_{priority}', json.dumps(email_data))
        
        logger.info(f"✅ Email {email_id} queued for {to_email} via API")
        
        return jsonify({
            'success': True,
            'message': 'Email queued successfully',
            'data': {
                'id': email_id,
                'to': to_email,
                'subject': data.get('subject'),
                'status': 'queued',
                'created_at': email.created_at.isoformat()
            }
        }), 202
        
    except Exception as e:
        logger.error(f"Send email error: {e}", exc_info=True)
        db.session.rollback()
        return jsonify({
            'error': 'server_error',
            'message': str(e)
        }), 500


@api_v1_bp.route('/emails/<email_id>', methods=['GET'])
@require_api_key_legacy(['emails.read'])
@rate_limit_decorator
def get_email(email_id):
    """Get email details"""
    try:
        email = Email.query.filter_by(
            id=email_id,
            organization_id=g.organization_id
        ).first()
        
        if not email:
            return jsonify({
                'error': 'not_found',
                'message': 'Email not found'
            }), 404
        
        return jsonify({
            'success': True,
            'data': email.to_dict()
        }), 200
        
    except Exception as e:
        logger.error(f"Get email error: {e}")
        return jsonify({
            'error': 'server_error',
            'message': str(e)
        }), 500


@api_v1_bp.route('/emails', methods=['GET'])
@require_api_key_legacy(['emails.read'])
@rate_limit_decorator
def list_emails():
    """List emails with pagination"""
    try:
        status = request.args.get('status')
        limit = min(int(request.args.get('limit', 50)), 100)
        offset = int(request.args.get('offset', 0))
        
        query = Email.query.filter_by(organization_id=g.organization_id)
        
        if status:
            query = query.filter_by(status=status)
        
        total = query.count()
        emails = query.order_by(Email.created_at.desc()).limit(limit).offset(offset).all()
        
        return jsonify({
            'success': True,
            'data': [email.to_dict() for email in emails],
            'pagination': {
                'total': total,
                'limit': limit,
                'offset': offset,
                'has_more': (offset + limit) < total
            }
        }), 200
        
    except Exception as e:
        logger.error(f"List emails error: {e}")
        return jsonify({
            'error': 'server_error',
            'message': str(e)
        }), 500


# ============================================
# CONTACTS API
# ============================================

@api_v1_bp.route('/contacts', methods=['POST'])
@require_api_key_legacy(['contacts.write'])
@rate_limit_decorator
def create_contact():
    """Create a new contact"""
    try:
        data = request.json
        
        if not data.get('email'):
            return jsonify({
                'error': 'validation_error',
                'message': 'Email is required'
            }), 400
        
        # Check if contact exists
        existing = Contact.query.filter_by(
            organization_id=g.organization_id,
            email=data['email'].lower()
        ).first()
        
        if existing:
            return jsonify({
                'error': 'conflict',
                'message': 'Contact with this email already exists',
                'data': existing.to_dict()
            }), 409
        
        # Create contact
        contact = Contact(
            organization_id=g.organization_id,
            email=data['email'],
            first_name=data.get('first_name'),
            last_name=data.get('last_name'),
            phone=data.get('phone'),
            company=data.get('company'),
            tags=data.get('tags', []),
            custom_fields=data.get('custom_fields', {})
        )
        
        db.session.add(contact)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Contact created successfully',
            'data': contact.to_dict()
        }), 201
        
    except Exception as e:
        logger.error(f"Create contact error: {e}")
        db.session.rollback()
        return jsonify({
            'error': 'server_error',
            'message': str(e)
        }), 500


@api_v1_bp.route('/contacts/<contact_id>', methods=['GET'])
@require_api_key_legacy(['contacts.read'])
@rate_limit_decorator
def get_contact(contact_id):
    """Get contact by ID"""
    try:
        contact = Contact.query.filter_by(
            id=contact_id,
            organization_id=g.organization_id
        ).first()
        
        if not contact:
            return jsonify({
                'error': 'not_found',
                'message': 'Contact not found'
            }), 404
        
        return jsonify({
            'success': True,
            'data': contact.to_dict()
        }), 200
        
    except Exception as e:
        logger.error(f"Get contact error: {e}")
        return jsonify({
            'error': 'server_error',
            'message': str(e)
        }), 500


@api_v1_bp.route('/contacts/<contact_id>', methods=['PUT'])
@require_api_key_legacy(['contacts.write'])
@rate_limit_decorator
def update_contact(contact_id):
    """Update contact"""
    try:
        contact = Contact.query.filter_by(
            id=contact_id,
            organization_id=g.organization_id
        ).first()
        
        if not contact:
            return jsonify({
                'error': 'not_found',
                'message': 'Contact not found'
            }), 404
        
        data = request.json
        
        # Update fields
        if 'first_name' in data:
            contact.first_name = data['first_name']
        if 'last_name' in data:
            contact.last_name = data['last_name']
        if 'phone' in data:
            contact.phone = data['phone']
        if 'company' in data:
            contact.company = data['company']
        if 'tags' in data:
            contact.tags = data['tags']
        if 'custom_fields' in data:
            contact.custom_fields = data['custom_fields']
        if 'status' in data:
            contact.status = data['status']
        
        contact.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Contact updated successfully',
            'data': contact.to_dict()
        }), 200
        
    except Exception as e:
        logger.error(f"Update contact error: {e}")
        db.session.rollback()
        return jsonify({
            'error': 'server_error',
            'message': str(e)
        }), 500


@api_v1_bp.route('/contacts/<contact_id>', methods=['DELETE'])
@require_api_key_legacy(['contacts.write'])
@rate_limit_decorator
def delete_contact(contact_id):
    """Delete contact"""
    try:
        contact = Contact.query.filter_by(
            id=contact_id,
            organization_id=g.organization_id
        ).first()
        
        if not contact:
            return jsonify({
                'error': 'not_found',
                'message': 'Contact not found'
            }), 404
        
        db.session.delete(contact)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Contact deleted successfully'
        }), 200
        
    except Exception as e:
        logger.error(f"Delete contact error: {e}")
        db.session.rollback()
        return jsonify({
            'error': 'server_error',
            'message': str(e)
        }), 500


@api_v1_bp.route('/contacts', methods=['GET'])
@require_api_key_legacy(['contacts.read'])
@rate_limit_decorator
def list_contacts():
    """List contacts"""
    try:
        status = request.args.get('status')
        limit = min(int(request.args.get('limit', 50)), 100)
        offset = int(request.args.get('offset', 0))
        
        query = Contact.query.filter_by(organization_id=g.organization_id)
        
        if status:
            query = query.filter_by(status=status)
        
        total = query.count()
        contacts = query.order_by(Contact.created_at.desc()).limit(limit).offset(offset).all()
        
        return jsonify({
            'success': True,
            'data': [contact.to_dict() for contact in contacts],
            'pagination': {
                'total': total,
                'limit': limit,
                'offset': offset,
                'has_more': (offset + limit) < total
            }
        }), 200
        
    except Exception as e:
        logger.error(f"List contacts error: {e}")
        return jsonify({
            'error': 'server_error',
            'message': str(e)
        }), 500


# ============================================
# CAMPAIGNS API
# ============================================

@api_v1_bp.route('/campaigns', methods=['POST'])
@require_api_key_legacy(['campaigns.write'])
@rate_limit_decorator
def create_campaign():
    """Create a new campaign"""
    try:
        data = request.json
        
        if not data.get('name'):
            return jsonify({
                'error': 'validation_error',
                'message': 'Campaign name is required'
            }), 400
        
        campaign = Campaign()
        campaign.id = str(uuid.uuid4())
        campaign.organization_id = g.organization_id
        campaign.name = data['name']
        campaign.subject = data.get('subject')
        campaign.from_email = data.get('from_email')
        campaign.status = 'draft'
        campaign.created_at = datetime.utcnow()
        
        db.session.add(campaign)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Campaign created successfully',
            'data': campaign.to_dict()
        }), 201
        
    except Exception as e:
        logger.error(f"Create campaign error: {e}")
        db.session.rollback()
        return jsonify({
            'error': 'server_error',
            'message': str(e)
        }), 500


@api_v1_bp.route('/campaigns/<campaign_id>', methods=['GET'])
@require_api_key_legacy(['campaigns.read'])
@rate_limit_decorator
def get_campaign(campaign_id):
    """Get campaign by ID"""
    try:
        campaign = Campaign.query.filter_by(
            id=campaign_id,
            organization_id=g.organization_id
        ).first()
        
        if not campaign:
            return jsonify({
                'error': 'not_found',
                'message': 'Campaign not found'
            }), 404
        
        return jsonify({
            'success': True,
            'data': campaign.to_dict()
        }), 200
        
    except Exception as e:
        logger.error(f"Get campaign error: {e}")
        return jsonify({
            'error': 'server_error',
            'message': str(e)
        }), 500


@api_v1_bp.route('/campaigns', methods=['GET'])
@require_api_key_legacy(['campaigns.read'])
@rate_limit_decorator
def list_campaigns():
    """List all campaigns"""
    try:
        limit = min(int(request.args.get('limit', 50)), 100)
        offset = int(request.args.get('offset', 0))
        
        query = Campaign.query.filter_by(organization_id=g.organization_id)
        
        total = query.count()
        campaigns = query.order_by(Campaign.created_at.desc()).limit(limit).offset(offset).all()
        
        return jsonify({
            'success': True,
            'data': [campaign.to_dict() for campaign in campaigns],
            'pagination': {
                'total': total,
                'limit': limit,
                'offset': offset,
                'has_more': (offset + limit) < total
            }
        }), 200
        
    except Exception as e:
        logger.error(f"List campaigns error: {e}")
        return jsonify({
            'error': 'server_error',
            'message': str(e)
        }), 500


# ============================================
# UTILITY ENDPOINTS
# ============================================

@api_v1_bp.route('/ping', methods=['GET'])
def ping():
    """Health check endpoint (no auth required)"""
    return jsonify({
        'success': True,
        'message': 'pong',
        'timestamp': datetime.utcnow().isoformat(),
        'version': 'v1'
    }), 200


@api_v1_bp.route('/me', methods=['GET'])
@require_api_key_legacy([])
def get_api_info():
    """Get current API key information"""
    return jsonify({
        'success': True,
        'data': {
            'organization_id': g.organization_id,
            'api_key': g.api_key.to_dict() if hasattr(g.api_key, 'to_dict') else {
                'organization_id': g.organization_id,
                'type': 'legacy',
                'scopes': ['*']
            }
        }
    }), 200
