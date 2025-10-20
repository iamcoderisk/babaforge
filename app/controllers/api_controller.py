"""
API Controller - Email Sending API
"""
from flask import Blueprint, request, jsonify
from app.services.email.email_service import EmailService
from app import limiter
import logging
import uuid

logger = logging.getLogger(__name__)

api_bp = Blueprint('api', __name__)

email_service = EmailService()

@api_bp.route('/send', methods=['POST'])
@limiter.limit("100 per minute")
def send_email():
    """Send single email"""
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data.get('to') or not data.get('from') or not data.get('subject'):
            return jsonify({
                'success': False,
                'error': 'Missing required fields: to, from, subject'
            }), 400
        
        # Generate email ID
        email_id = str(uuid.uuid4())
        
        # Queue email
        result = email_service.queue_email({
            'id': email_id,
            'to': data['to'],
            'from': data['from'],
            'subject': data['subject'],
            'text_body': data.get('text_body'),
            'html_body': data.get('html_body'),
            'priority': data.get('priority', 5),
            'headers': data.get('headers', {})
        })
        
        return jsonify({
            'success': True,
            'email_id': email_id,
            'status': 'queued'
        })
    
    except Exception as e:
        logger.error(f"Error sending email: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api_bp.route('/send/bulk', methods=['POST'])
@limiter.limit("10 per minute")
def send_bulk():
    """Send bulk emails"""
    try:
        data = request.get_json()
        emails = data.get('emails', [])
        
        if len(emails) > 10000:
            return jsonify({
                'success': False,
                'error': 'Maximum 10,000 emails per bulk request'
            }), 400
        
        batch_id = str(uuid.uuid4())
        email_ids = []
        
        for email_data in emails:
            email_id = str(uuid.uuid4())
            email_ids.append(email_id)
            
            email_data['id'] = email_id
            email_data['batch_id'] = batch_id
            email_service.queue_email(email_data)
        
        return jsonify({
            'success': True,
            'batch_id': batch_id,
            'queued': len(email_ids),
            'email_ids': email_ids
        })
    
    except Exception as e:
        logger.error(f"Error sending bulk: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api_bp.route('/status/<email_id>', methods=['GET'])
def get_status(email_id):
    """Get email status"""
    try:
        status = email_service.get_email_status(email_id)
        
        if not status:
            return jsonify({
                'success': False,
                'error': 'Email not found'
            }), 404
        
        return jsonify({
            'success': True,
            'email_id': email_id,
            'status': status
        })
    
    except Exception as e:
        logger.error(f"Error getting status: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api_bp.route('/metrics', methods=['GET'])
def get_metrics():
    """Get system metrics"""
    try:
        metrics = email_service.get_metrics()
        
        return jsonify({
            'success': True,
            'metrics': metrics
        })
    
    except Exception as e:
        logger.error(f"Error getting metrics: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
