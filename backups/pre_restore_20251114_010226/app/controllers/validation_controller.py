from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from app.services.email_validator import email_validator
from app.models.contact import Contact
from app import db

validation_bp = Blueprint('validation', __name__, url_prefix='/dashboard/validation')

@validation_bp.route('/')
@login_required
def index():
    """Email validation dashboard"""
    return render_template('dashboard/validation/index.html')

@validation_bp.route('/validate-single', methods=['POST'])
@login_required
def validate_single():
    """Validate single email"""
    data = request.get_json()
    email = data.get('email')
    
    if not email:
        return jsonify({'success': False, 'error': 'Email required'}), 400
    
    org = current_user.organization
    
    # Check cache first
    cached = email_validator.get_cached_validation(email, org.id)
    if cached:
        return jsonify({'success': True, **cached})
    
    # Validate
    result = email_validator.validate_email(email, org.id, deep_check=True)
    
    return jsonify({'success': True, **result})

@validation_bp.route('/validate-bulk', methods=['POST'])
@login_required
def validate_bulk():
    """Validate multiple emails"""
    data = request.get_json()
    emails = data.get('emails', [])
    
    if not emails:
        return jsonify({'success': False, 'error': 'No emails provided'}), 400
    
    org = current_user.organization
    
    results = email_validator.bulk_validate(emails, org.id)
    
    return jsonify({
        'success': True,
        'results': results,
        'summary': {
            'total': len(results),
            'valid': len([r for r in results if r['status'] == 'deliverable']),
            'risky': len([r for r in results if r['status'] == 'risky']),
            'invalid': len([r for r in results if r['status'] in ['invalid', 'undeliverable']])
        }
    })

@validation_bp.route('/validate-contacts', methods=['POST'])
@login_required
def validate_contacts():
    """Validate all contacts"""
    org = current_user.organization
    
    contacts = Contact.query.filter_by(
        organization_id=org.id,
        status='active'
    ).all()
    
    emails = [c.email for c in contacts]
    results = email_validator.bulk_validate(emails, org.id)
    
    # Update contact statuses
    for result in results:
        if result['status'] in ['invalid', 'undeliverable']:
            contact = Contact.query.filter_by(
                organization_id=org.id,
                email=result['email']
            ).first()
            
            if contact:
                contact.status = 'invalid'
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'validated': len(results),
        'summary': {
            'total': len(results),
            'valid': len([r for r in results if r['status'] == 'deliverable']),
            'risky': len([r for r in results if r['status'] == 'risky']),
            'invalid': len([r for r in results if r['status'] in ['invalid', 'undeliverable']])
        }
    })
