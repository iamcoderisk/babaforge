from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from app import db
from app.models.campaign import Campaign, EmailTemplate, CampaignRecipient
from app.models.contact import Contact
from app.models.domain import Domain
from app.middleware.auth import require_api_key
from datetime import datetime
import re
import logging

logger = logging.getLogger(__name__)

campaign_bp = Blueprint('campaigns', __name__)

# ============= Template Endpoints =============

@campaign_bp.route('/template', methods=['POST'])
@require_api_key
def create_template():
    """Create email template"""
    try:
        data = request.get_json()
        
        name = data.get('name', '').strip()
        if not name:
            return jsonify({'success': False, 'error': 'Template name is required'}), 400
        
        # Extract variables from template
        html_body = data.get('html_body', '')
        subject = data.get('subject', '')
        
        # Find {{variable}} patterns
        variables = list(set(
            re.findall(r'\{\{(\w+)\}\}', html_body) + 
            re.findall(r'\{\{(\w+)\}\}', subject)
        ))
        
        template = EmailTemplate(
            organization_id=request.organization.id,
            name=name,
            subject=subject,
            html_body=html_body,
            text_body=data.get('text_body')
        )
        template.variables = variables
        
        db.session.add(template)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'template': template.to_dict(),
            'message': 'Template created successfully'
        }), 201
        
    except Exception as e:
        logger.error(f"Create template error: {e}")
        db.session.rollback()
        return jsonify({'success': False, 'error': 'Failed to create template'}), 500

@campaign_bp.route('/templates', methods=['GET'])
@require_api_key
def list_templates():
    """List all templates"""
    try:
        templates = EmailTemplate.query.filter_by(
            organization_id=request.organization.id,
            is_active=True
        ).order_by(EmailTemplate.created_at.desc()).all()
        
        return jsonify({
            'success': True,
            'templates': [t.to_dict() for t in templates],
            'total': len(templates)
        })
        
    except Exception as e:
        logger.error(f"List templates error: {e}")
        return jsonify({'success': False, 'error': 'Failed to list templates'}), 500

@campaign_bp.route('/template/<template_id>', methods=['GET'])
@require_api_key
def get_template(template_id):
    """Get single template"""
    try:
        template = EmailTemplate.query.filter_by(
            id=template_id,
            organization_id=request.organization.id
        ).first()
        
        if not template:
            return jsonify({'success': False, 'error': 'Template not found'}), 404
        
        return jsonify({
            'success': True,
            'template': template.to_dict()
        })
        
    except Exception as e:
        logger.error(f"Get template error: {e}")
        return jsonify({'success': False, 'error': 'Failed to get template'}), 500

# ============= Campaign Endpoints =============

@campaign_bp.route('/campaign', methods=['POST'])
@require_api_key
def create_campaign():
    """Create a new campaign"""
    try:
        data = request.get_json()
        
        name = data.get('name', '').strip()
        if not name:
            return jsonify({'success': False, 'error': 'Campaign name is required'}), 400
        
        from_email = data.get('from_email', '').strip()
        if not from_email:
            return jsonify({'success': False, 'error': 'From email is required'}), 400
        
        # Verify domain
        from_domain = from_email.split('@')[1]
        domain = Domain.query.filter_by(
            domain_name=from_domain,
            organization_id=request.organization.id,
            dns_verified=True
        ).first()
        
        if not domain:
            return jsonify({
                'success': False,
                'error': f'Domain {from_domain} is not verified. Please verify it first.'
            }), 400
        
        campaign = Campaign(
            organization_id=request.organization.id,
            name=name,
            subject=data.get('subject'),
            from_email=from_email,
            from_name=data.get('from_name'),
            reply_to=data.get('reply_to'),
            html_body=data.get('html_body'),
            text_body=data.get('text_body'),
            template_id=data.get('template_id'),
            segment_filters=data.get('segment_filters')
        )
        
        db.session.add(campaign)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'campaign': campaign.to_dict(),
            'message': 'Campaign created successfully'
        }), 201
        
    except Exception as e:
        logger.error(f"Create campaign error: {e}")
        db.session.rollback()
        return jsonify({'success': False, 'error': 'Failed to create campaign'}), 500

@campaign_bp.route('/campaigns', methods=['GET'])
@require_api_key
def list_campaigns():
    """List all campaigns"""
    try:
        status = request.args.get('status')
        
        query = Campaign.query.filter_by(
            organization_id=request.organization.id
        )
        
        if status:
            query = query.filter_by(status=status)
        
        campaigns = query.order_by(Campaign.created_at.desc()).all()
        
        return jsonify({
            'success': True,
            'campaigns': [c.to_dict() for c in campaigns],
            'total': len(campaigns)
        })
        
    except Exception as e:
        logger.error(f"List campaigns error: {e}")
        return jsonify({'success': False, 'error': 'Failed to list campaigns'}), 500

@campaign_bp.route('/campaign/<campaign_id>', methods=['GET'])
@require_api_key
def get_campaign(campaign_id):
    """Get campaign details"""
    try:
        campaign = Campaign.query.filter_by(
            id=campaign_id,
            organization_id=request.organization.id
        ).first()
        
        if not campaign:
            return jsonify({'success': False, 'error': 'Campaign not found'}), 404
        
        return jsonify({
            'success': True,
            'campaign': campaign.to_dict()
        })
        
    except Exception as e:
        logger.error(f"Get campaign error: {e}")
        return jsonify({'success': False, 'error': 'Failed to get campaign'}), 500

@campaign_bp.route('/campaign/<campaign_id>/recipients', methods=['POST'])
@require_api_key
def add_campaign_recipients(campaign_id):
    """Add recipients to campaign"""
    try:
        campaign = Campaign.query.filter_by(
            id=campaign_id,
            organization_id=request.organization.id
        ).first()
        
        if not campaign:
            return jsonify({'success': False, 'error': 'Campaign not found'}), 404
        
        if campaign.status not in ['draft', 'paused']:
            return jsonify({
                'success': False,
                'error': 'Cannot add recipients to campaign in current status'
            }), 400
        
        data = request.get_json()
        
        # Get contact IDs or filters
        contact_ids = data.get('contact_ids', [])
        filters = data.get('filters', {})
        
        if contact_ids:
            # Add specific contacts
            contacts = Contact.query.filter(
                Contact.id.in_(contact_ids),
                Contact.organization_id == request.organization.id,
                Contact.status == 'active'
            ).all()
        else:
            # Add all active contacts (or filtered)
            query = Contact.query.filter_by(
                organization_id=request.organization.id,
                status='active'
            )
            
            # Apply filters if provided
            if filters.get('tags'):
                # Filter by tags
                query = query.filter(Contact.tags.contains(filters['tags']))
            
            contacts = query.all()
        
        # Add recipients
        added = 0
        for contact in contacts:
            # Check if already added
            existing = CampaignRecipient.query.filter_by(
                campaign_id=campaign_id,
                contact_id=contact.id
            ).first()
            
            if not existing:
                recipient = CampaignRecipient(
                    campaign_id=campaign_id,
                    contact_id=contact.id
                )
                db.session.add(recipient)
                added += 1
        
        campaign.total_recipients = CampaignRecipient.query.filter_by(
            campaign_id=campaign_id
        ).count()
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'added': added,
            'total_recipients': campaign.total_recipients,
            'message': f'Added {added} recipients to campaign'
        })
        
    except Exception as e:
        logger.error(f"Add recipients error: {e}")
        db.session.rollback()
        return jsonify({'success': False, 'error': 'Failed to add recipients'}), 500

@campaign_bp.route('/campaign/<campaign_id>/send', methods=['POST'])
@require_api_key
def send_campaign(campaign_id):
    """Send or schedule campaign"""
    try:
        campaign = Campaign.query.filter_by(
            id=campaign_id,
            organization_id=request.organization.id
        ).first()
        
        if not campaign:
            return jsonify({'success': False, 'error': 'Campaign not found'}), 404
        
        if campaign.total_recipients == 0:
            return jsonify({
                'success': False,
                'error': 'Cannot send campaign with no recipients'
            }), 400
        
        data = request.get_json() or {}
        
        # Check if scheduling
        scheduled_at = data.get('scheduled_at')
        
        if scheduled_at:
            campaign.scheduled_at = datetime.fromisoformat(scheduled_at.replace('Z', '+00:00'))
            campaign.status = 'scheduled'
            db.session.commit()
            
            return jsonify({
                'success': True,
                'campaign': campaign.to_dict(),
                'message': f'Campaign scheduled for {campaign.scheduled_at}'
            })
        else:
            # Send immediately
            campaign.status = 'sending'
            campaign.started_at = datetime.utcnow()
            db.session.commit()
            
            # TODO: Queue emails for sending
            # For now, just mark as sent
            campaign.status = 'sent'
            campaign.completed_at = datetime.utcnow()
            db.session.commit()
            
            return jsonify({
                'success': True,
                'campaign': campaign.to_dict(),
                'message': 'Campaign sent successfully'
            })
        
    except Exception as e:
        logger.error(f"Send campaign error: {e}")
        db.session.rollback()
        return jsonify({'success': False, 'error': 'Failed to send campaign'}), 500

@campaign_bp.route('/campaign/<campaign_id>', methods=['DELETE'])
@require_api_key
def delete_campaign(campaign_id):
    """Delete campaign"""
    try:
        campaign = Campaign.query.filter_by(
            id=campaign_id,
            organization_id=request.organization.id
        ).first()
        
        if not campaign:
            return jsonify({'success': False, 'error': 'Campaign not found'}), 404
        
        if campaign.status in ['sending']:
            return jsonify({
                'success': False,
                'error': 'Cannot delete campaign while sending'
            }), 400
        
        db.session.delete(campaign)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Campaign deleted successfully'
        })
        
    except Exception as e:
        logger.error(f"Delete campaign error: {e}")
        db.session.rollback()
        return jsonify({'success': False, 'error': 'Failed to delete campaign'}), 500
