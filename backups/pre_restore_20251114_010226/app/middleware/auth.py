from functools import wraps
from flask import request, jsonify
from app.models.organization import Organization
from app.models.domain import Domain
from datetime import date

def require_api_key(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        
        if not api_key:
            return jsonify({
                'success': False,
                'error': 'API key required. Include X-API-Key header.'
            }), 401
        
        org = Organization.query.filter_by(api_key=api_key, is_active=True).first()
        if not org:
            return jsonify({
                'success': False,
                'error': 'Invalid or inactive API key'
            }), 401
        
        request.organization = org
        return f(*args, **kwargs)
    
    return decorated_function

def validate_sender_domain(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        data = request.get_json()
        sender_email = data.get('from', '')
        
        if not '@' in sender_email:
            return jsonify({
                'success': False,
                'error': 'Invalid sender email format'
            }), 400
        
        sender_domain = sender_email.split('@')[1].lower()
        
        domain = Domain.query.filter_by(
            domain_name=sender_domain,
            organization_id=request.organization.id,
            dns_verified=True,
            is_active=True
        ).first()
        
        if not domain:
            return jsonify({
                'success': False,
                'error': f'Domain {sender_domain} is not verified or authorized.'
            }), 403
        
        request.domain = domain
        return f(*args, **kwargs)
    
    return decorated_function

def check_rate_limits(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        from app.models.domain import EmailUsage
        from app import db
        
        org = request.organization
        today = date.today()
        
        usage = EmailUsage.query.filter_by(
            organization_id=org.id,
            date=today
        ).first()
        
        if not usage:
            usage = EmailUsage(org.id, today)
            db.session.add(usage)
            db.session.commit()
        
        request.usage = usage
        return f(*args, **kwargs)
    
    return decorated_function
