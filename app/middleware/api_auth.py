from functools import wraps
from flask import request, jsonify, g
from app.models.api_key import APIKey
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


def require_api_key(required_scopes=None):
    """
    Decorator to require API key authentication
    Usage: @require_api_key(['emails.send', 'emails.read'])
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Get API key from header
            auth_header = request.headers.get('Authorization', '')
            
            if not auth_header.startswith('Bearer '):
                return jsonify({
                    'error': 'unauthorized',
                    'message': 'Missing or invalid Authorization header. Use: Authorization: Bearer YOUR_API_KEY'
                }), 401
            
            api_key_value = auth_header.replace('Bearer ', '').strip()
            
            if not api_key_value:
                return jsonify({
                    'error': 'unauthorized',
                    'message': 'API key is required'
                }), 401
            
            # Extract key prefix to find record
            try:
                key_prefix = '_'.join(api_key_value.split('_')[:3])  # sb_live_xxxxx
            except:
                return jsonify({
                    'error': 'unauthorized',
                    'message': 'Invalid API key format'
                }), 401
            
            # Find API key record
            api_key = APIKey.query.filter_by(key_prefix=key_prefix).first()
            
            if not api_key:
                return jsonify({
                    'error': 'unauthorized',
                    'message': 'Invalid API key'
                }), 401
            
            # Verify key
            if not api_key.verify_key(api_key_value):
                return jsonify({
                    'error': 'unauthorized',
                    'message': 'Invalid API key'
                }), 401
            
            # Check if active
            if not api_key.is_active:
                return jsonify({
                    'error': 'unauthorized',
                    'message': 'API key is inactive'
                }), 401
            
            # Check expiration
            if api_key.expires_at and api_key.expires_at < datetime.utcnow():
                return jsonify({
                    'error': 'unauthorized',
                    'message': 'API key has expired'
                }), 401
            
            # Check scopes
            if required_scopes:
                for scope in required_scopes:
                    if not api_key.has_scope(scope):
                        return jsonify({
                            'error': 'forbidden',
                            'message': f'API key does not have required scope: {scope}',
                            'required_scopes': required_scopes,
                            'your_scopes': api_key.scopes
                        }), 403
            
            # Update last used
            try:
                api_key.last_used_at = datetime.utcnow()
                api_key.last_used_ip = request.remote_addr
                api_key.usage_count += 1
                from app import db
                db.session.commit()
            except Exception as e:
                logger.error(f"Failed to update API key usage: {e}")
                from app import db
                db.session.rollback()
            
            # Store in g for use in request
            g.api_key = api_key
            g.organization_id = api_key.organization_id
            
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator
