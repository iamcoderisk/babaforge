"""
Email Controller - Email Management
"""
from flask import Blueprint, render_template, jsonify, request
from app.models.email import Email
from app import db
import logging

logger = logging.getLogger(__name__)

email_bp = Blueprint('emails', __name__)

@email_bp.route('/')
def index():
    """Email list page"""
    return render_template('email/list.html')

@email_bp.route('/list')
def list_emails():
    """Get email list with pagination"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 50, type=int)
        status = request.args.get('status')
        
        # Try to query database
        try:
            query = Email.query
            
            if status:
                query = query.filter_by(status=status)
            
            pagination = query.order_by(
                Email.created_at.desc()
            ).paginate(
                page=page,
                per_page=per_page,
                error_out=False
            )
            
            emails = [email.to_dict() for email in pagination.items]
            
            return jsonify({
                'success': True,
                'emails': emails,
                'total': pagination.total,
                'pages': pagination.pages,
                'current_page': page
            })
        
        except Exception as db_error:
            # Database not initialized yet, return empty list
            logger.warning(f"Database query failed: {db_error}")
            return jsonify({
                'success': True,
                'emails': [],
                'total': 0,
                'pages': 0,
                'current_page': 1
            })
    
    except Exception as e:
        logger.error(f"Error listing emails: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@email_bp.route('/<email_id>')
def get_email(email_id):
    """Get email details"""
    try:
        email = Email.query.filter_by(id=email_id).first()
        
        if not email:
            return jsonify({
                'success': False,
                'error': 'Email not found'
            }), 404
        
        return jsonify({
            'success': True,
            'email': email.to_dict()
        })
    
    except Exception as e:
        logger.error(f"Error getting email: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
