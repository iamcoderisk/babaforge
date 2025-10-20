# ============= app/middleware/auth.py =============
"""
Authentication Middleware
"""
from functools import wraps
from flask import request, jsonify, current_app

from app.models.database import Organization
from app.config.settings import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)

def require_api_key(f):
    """Require valid API key"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get(settings.API_KEY_HEADER)
        
        if not api_key:
            return jsonify({'error': 'Missing API key'}), 401
        
        # Validate API key
        db = current_app.session()
        org = db.query(Organization).filter_by(api_key=api_key).first()
        
        if not org:
            return jsonify({'error': 'Invalid API key'}), 401
        
        if org.status != 'active':
            return jsonify({'error': 'Organization inactive'}), 403
        
        # Pass org_id to the function
        return f(org_id=org.id, *args, **kwargs)
    
    return decorated_function

def require_admin(f):
    """Require admin authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Simple admin key check (enhance with JWT in production)
        admin_key = request.headers.get('X-Admin-Key')
        
        if admin_key != settings.SECRET_KEY:
            return jsonify({'error': 'Unauthorized'}), 401
        
        return f(*args, **kwargs)
    
    return decorated_function