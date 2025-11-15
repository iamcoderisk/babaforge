from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from flask_login import login_required, current_user
from app import db
from app.models.api_key import APIKey, SMTPCredential
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

api_keys_bp = Blueprint('api_keys', __name__, url_prefix='/dashboard/api-keys')

@api_keys_bp.route('/')
@login_required
def index():
    """List all API keys"""
    try:
        api_keys = APIKey.query.filter_by(
            organization_id=current_user.organization_id
        ).order_by(APIKey.created_at.desc()).all()
        
        smtp_creds = SMTPCredential.query.filter_by(
            organization_id=current_user.organization_id
        ).order_by(SMTPCredential.created_at.desc()).all()
        
        return render_template('dashboard/api_keys/index.html', 
                             api_keys=api_keys,
                             smtp_credentials=smtp_creds)
    except Exception as e:
        logger.error(f"List API keys error: {e}")
        return render_template('dashboard/api_keys/index.html', 
                             api_keys=[],
                             smtp_credentials=[])

@api_keys_bp.route('/create', methods=['POST'])
@login_required
def create():
    """Create new API key"""
    try:
        data = request.json
        name = data.get('name', 'Unnamed Key')
        scopes = data.get('scopes', ['emails.send', 'emails.read'])
        
        api_key = APIKey(
            organization_id=current_user.organization_id,
            name=name,
            scopes=scopes
        )
        
        db.session.add(api_key)
        db.session.commit()
        
        # Return the full key (only shown once!)
        return jsonify({
            'success': True,
            'message': 'API key created successfully',
            'data': api_key.to_dict(include_key=True)
        }), 201
        
    except Exception as e:
        logger.error(f"Create API key error: {e}")
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api_keys_bp.route('/<key_id>/delete', methods=['POST'])
@login_required
def delete(key_id):
    """Delete API key"""
    try:
        api_key = APIKey.query.filter_by(
            id=key_id,
            organization_id=current_user.organization_id
        ).first()
        
        if not api_key:
            return jsonify({
                'success': False,
                'error': 'API key not found'
            }), 404
        
        db.session.delete(api_key)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'API key deleted successfully'
        }), 200
        
    except Exception as e:
        logger.error(f"Delete API key error: {e}")
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api_keys_bp.route('/smtp/create', methods=['POST'])
@login_required
def create_smtp():
    """Create SMTP credentials"""
    try:
        data = request.json
        name = data.get('name', 'SMTP Credentials')
        
        smtp_cred = SMTPCredential(
            organization_id=current_user.organization_id,
            name=name
        )
        
        db.session.add(smtp_cred)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'SMTP credentials created successfully',
            'data': smtp_cred.to_dict(include_password=True)
        }), 201
        
    except Exception as e:
        logger.error(f"Create SMTP creds error: {e}")
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
