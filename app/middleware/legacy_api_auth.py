"""
Support for legacy API keys from organizations table
"""
from functools import wraps
from flask import request, jsonify, g
from app.models.api_key import APIKey
from app.models.organization import Organization
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


def require_api_key_legacy(required_scopes=None):
    """
    Support both new API keys (api_keys table) and legacy keys (organizations table)
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
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
            
            # Try new system first (keys starting with sb_live_)
            if api_key_value.startswith('sb_live_'):
                try:
                    key_prefix = '_'.join(api_key_value.split('_')[:3])
                    api_key = APIKey.query.filter_by(key_prefix=key_prefix).first()
                    
                    if api_key and api_key.verify_key(api_key_value):
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
                        
                        # Update usage
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
                        
                        g.api_key = api_key
                        g.organization_id = api_key.organization_id
                        logger.info(f"New API key authenticated for org {api_key.organization_id}")
                        return f(*args, **kwargs)
                except Exception as e:
                    logger.error(f"New API key verification error: {e}")
            
            # Try legacy system (organizations.api_key)
            # Keys starting with 'sb_' or 'sk_live_' from old system
            try:
                org = Organization.query.filter_by(api_key=api_key_value).first()
                
                if org:
                    if not org.is_active:
                        return jsonify({
                            'error': 'unauthorized',
                            'message': 'Organization is inactive'
                        }), 401
                    
                    # Create a fake api_key object for compatibility
                    class LegacyAPIKey:
                        def __init__(self, org):
                            self.id = org.id
                            self.organization_id = org.id
                            self.scopes = ['*']  # Legacy keys have all permissions
                            self.is_active = True
                            self.rate_limit_per_minute = 100
                            self.rate_limit_per_hour = 1000
                            self.rate_limit_per_day = 10000
                        
                        def has_scope(self, scope):
                            return True  # Legacy keys have full access
                        
                        def to_dict(self):
                            return {
                                'id': self.id,
                                'organization_id': self.organization_id,
                                'scopes': ['*'],
                                'type': 'legacy',
                                'rate_limits': {
                                    'per_minute': self.rate_limit_per_minute,
                                    'per_hour': self.rate_limit_per_hour,
                                    'per_day': self.rate_limit_per_day
                                }
                            }
                    
                    g.api_key = LegacyAPIKey(org)
                    g.organization_id = org.id
                    logger.info(f"✅ Legacy API key authenticated for org {org.id}")
                    return f(*args, **kwargs)
            except Exception as e:
                logger.error(f"Legacy API key verification error: {e}")
            
            # If we get here, authentication failed
            return jsonify({
                'error': 'unauthorized',
                'message': 'Invalid API key'
            }), 401
        
        return decorated_function
    return decorator
