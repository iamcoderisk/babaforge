from flask import Blueprint, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from app import db, redis_client
from sqlalchemy import text
import json
import uuid
import logging
from functools import wraps

logger = logging.getLogger(__name__)

api_bp = Blueprint('api', __name__, url_prefix='/api')

# API Key Authentication Decorator
def require_api_key(f):
    """Decorator for API key authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        
        if not api_key:
            return jsonify({'success': False, 'error': 'API key required'}), 401
        
        try:
            result = db.session.execute(
                text("SELECT id, name FROM organizations WHERE api_key = :api_key"),
                {'api_key': api_key}
            )
            org = result.fetchone()
            
            if not org:
                return jsonify({'success': False, 'error': 'Invalid API key'}), 401
            
            request.org_id = org[0]
            request.org_name = org[1]
            
            return f(*args, **kwargs)
            
        except Exception as e:
            logger.error(f"API auth error: {e}")
            return jsonify({'success': False, 'error': 'Authentication failed'}), 500
    
    return decorated_function

# ============= DASHBOARD API ENDPOINTS (Login Required) =============

@api_bp.route('/emails/send', methods=['POST'])
@login_required
def send_email():
    """Send email from dashboard"""
    try:
        from_name = request.form.get('from_name', 'noreply')
        from_domain = request.form.get('from_domain')
        to_email = request.form.get('to_email')
        subject = request.form.get('subject')
        html_body = request.form.get('html_body', '')
        
        if not to_email or not subject:
            return jsonify({'success': False, 'error': 'Missing required fields'}), 400
        
        from_email = f"{from_name}@{from_domain}" if from_domain else f"{from_name}@sendbaba.com"
        email_id = str(uuid.uuid4())
        
        # Save to database
        db.session.execute(
            text("""
                INSERT INTO emails (
                    id, organization_id, sender, recipient,
                    subject, html_body, status, created_at
                )
                VALUES (:id, :org_id, :sender, :recipient, :subject, :html_body, 'queued', NOW())
            """),
            {
                'id': email_id,
                'org_id': current_user.organization_id,
                'sender': from_email,
                'recipient': to_email,
                'subject': subject,
                'html_body': html_body
            }
        )
        
        # Queue for sending
        email_data = {
            'id': email_id,
            'org_id': current_user.organization_id,
            'from': from_email,
            'to': to_email,
            'subject': subject,
            'html_body': html_body,
            'text_body': '',
            'priority': 10
        }
        
        redis_client.lpush('outgoing_10', json.dumps(email_data))
        db.session.commit()
        
        return jsonify({
            'success': True,
            'email_id': email_id,
            'message': 'Email queued successfully'
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Send email error: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500

@api_bp.route('/contacts/import', methods=['POST'])
@login_required
def import_contacts():
    """Import contacts from CSV"""
    try:
        if 'file' not in request.files:
            flash('No file uploaded', 'error')
            return redirect(url_for('contacts.list_contacts'))
        
        file = request.files['file']
        if not file.filename.endswith('.csv'):
            flash('Only CSV files allowed', 'error')
            return redirect(url_for('contacts.list_contacts'))
        
        import csv, io
        
        stream = io.StringIO(file.stream.read().decode("UTF8"), newline=None)
        csv_reader = csv.DictReader(stream)
        
        imported = 0
        for row in csv_reader:
            email = row.get('email', '').strip()
            name = row.get('name', '').strip()
            
            if not email:
                continue
            
            contact_id = str(uuid.uuid4())
            
            try:
                db.session.execute(
                    text("""
                        INSERT INTO contacts (id, organization_id, email, name, created_at)
                        VALUES (:id, :org_id, :email, :name, NOW())
                        ON CONFLICT DO NOTHING
                    """),
                    {'id': contact_id, 'org_id': current_user.organization_id, 'email': email, 'name': name}
                )
                imported += 1
            except:
                continue
        
        db.session.commit()
        flash(f'{imported} contacts imported', 'success')
        return redirect(url_for('contacts.list_contacts'))
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Import error: {e}", exc_info=True)
        flash('Import failed', 'error')
        return redirect(url_for('contacts.list_contacts'))

@api_bp.route('/contacts/<contact_id>/delete', methods=['POST'])
@login_required
def delete_contact(contact_id):
    """Delete a contact"""
    try:
        db.session.execute(
            text("DELETE FROM contacts WHERE id = :id AND organization_id = :org_id"),
            {'id': contact_id, 'org_id': current_user.organization_id}
        )
        db.session.commit()
        flash('Contact deleted', 'success')
        return redirect(url_for('contacts.list_contacts'))
    except Exception as e:
        db.session.rollback()
        flash('Delete failed', 'error')
        return redirect(url_for('contacts.list_contacts'))


# ============= PUBLIC API v1 ENDPOINTS (API Key Required) =============

@api_bp.route('/v1/send', methods=['POST'])
@require_api_key
def api_v1_send():
    """API v1 - Send single email"""
    try:
        data = request.get_json()
        
        to_email = data.get('to')
        from_email = data.get('from')
        subject = data.get('subject')
        html_body = data.get('html_body', '')
        text_body = data.get('text_body', '')
        
        if not all([to_email, from_email, subject]):
            return jsonify({'success': False, 'error': 'Missing required fields: to, from, subject'}), 400
        
        email_id = str(uuid.uuid4())
        
        # Save to database
        db.session.execute(
            text("""
                INSERT INTO emails (
                    id, organization_id, sender, recipient,
                    subject, html_body, status, created_at
                )
                VALUES (:id, :org_id, :sender, :recipient, :subject, :html_body, 'queued', NOW())
            """),
            {
                'id': email_id,
                'org_id': request.org_id,
                'sender': from_email,
                'recipient': to_email,
                'subject': subject,
                'html_body': html_body
            }
        )
        
        # Queue for sending
        email_data = {
            'id': email_id,
            'org_id': request.org_id,
            'from': from_email,
            'to': to_email,
            'subject': subject,
            'html_body': html_body,
            'text_body': text_body,
            'priority': 10
        }
        
        redis_client.lpush('outgoing_10', json.dumps(email_data))
        db.session.commit()
        
        logger.info(f"API: Email {email_id} queued for {to_email}")
        
        return jsonify({
            'success': True,
            'email_id': email_id,
            'message': 'Email queued successfully'
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"API v1 send error: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500

@api_bp.route('/v1/send/bulk', methods=['POST'])
@require_api_key
def api_v1_bulk_send():
    """API v1 - Send bulk emails"""
    try:
        data = request.get_json()
        emails = data.get('emails', [])
        
        if not emails:
            return jsonify({'success': False, 'error': 'No emails provided'}), 400
        
        if len(emails) > 10000:
            return jsonify({'success': False, 'error': 'Maximum 10,000 emails per request'}), 400
        
        queued_ids = []
        
        for email in emails:
            email_id = str(uuid.uuid4())
            
            db.session.execute(
                text("""
                    INSERT INTO emails (
                        id, organization_id, sender, recipient,
                        subject, html_body, status, created_at
                    )
                    VALUES (:id, :org_id, :sender, :recipient, :subject, :html_body, 'queued', NOW())
                """),
                {
                    'id': email_id,
                    'org_id': request.org_id,
                    'sender': email.get('from'),
                    'recipient': email.get('to'),
                    'subject': email.get('subject'),
                    'html_body': email.get('html_body', '')
                }
            )
            
            email_data = {
                'id': email_id,
                'org_id': request.org_id,
                'from': email.get('from'),
                'to': email.get('to'),
                'subject': email.get('subject'),
                'html_body': email.get('html_body', ''),
                'text_body': email.get('text_body', ''),
                'priority': 5
            }
            
            redis_client.lpush('outgoing_5', json.dumps(email_data))
            queued_ids.append(email_id)
        
        db.session.commit()
        
        logger.info(f"API: Bulk queued {len(queued_ids)} emails")
        
        return jsonify({
            'success': True,
            'queued': len(queued_ids),
            'email_ids': queued_ids
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"API v1 bulk send error: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500

@api_bp.route('/v1/usage', methods=['GET'])
@require_api_key
def api_v1_usage():
    """API v1 - Get usage stats"""
    try:
        result = db.session.execute(
            text("""
                SELECT 
                    COUNT(*) FILTER (WHERE created_at >= CURRENT_DATE) as today_sent,
                    COUNT(*) FILTER (WHERE created_at >= CURRENT_DATE - INTERVAL '30 days') as month_sent
                FROM emails
                WHERE organization_id = :org_id AND status = 'sent'
            """),
            {'org_id': request.org_id}
        )
        
        row = result.fetchone()
        
        return jsonify({
            'success': True,
            'usage': {
                'today': {'sent': row[0] or 0, 'failed': 0},
                'last_30_days': {'sent': row[1] or 0, 'failed': 0}
            }
        })
        
    except Exception as e:
        logger.error(f"API v1 usage error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@api_bp.route('/v1/contacts', methods=['GET', 'POST'])
@require_api_key
def api_v1_contacts():
    """API v1 - List or add contacts"""
    if request.method == 'GET':
        try:
            page = request.args.get('page', 1, type=int)
            per_page = min(request.args.get('per_page', 50, type=int), 100)
            
            result = db.session.execute(
                text("""
                    SELECT id, email, name, created_at
                    FROM contacts
                    WHERE organization_id = :org_id
                    ORDER BY created_at DESC
                    LIMIT :limit OFFSET :offset
                """),
                {'org_id': request.org_id, 'limit': per_page, 'offset': (page - 1) * per_page}
            )
            
            contacts = [{'id': r[0], 'email': r[1], 'name': r[2], 'created_at': r[3].isoformat()} for r in result]
            
            return jsonify({'success': True, 'contacts': contacts})
            
        except Exception as e:
            logger.error(f"API v1 list contacts error: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    else:  # POST
        try:
            data = request.get_json()
            contact_id = str(uuid.uuid4())
            
            db.session.execute(
                text("""
                    INSERT INTO contacts (id, organization_id, email, name, created_at)
                    VALUES (:id, :org_id, :email, :name, NOW())
                """),
                {
                    'id': contact_id,
                    'org_id': request.org_id,
                    'email': data.get('email'),
                    'name': f"{data.get('first_name', '')} {data.get('last_name', '')}".strip()
                }
            )
            
            db.session.commit()
            
            return jsonify({'success': True, 'contact_id': contact_id})
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"API v1 add contact error: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500

# ============= TEMPLATE PREVIEW ENDPOINT =============

@api_bp.route('/templates/preview/<template_name>')
def api_preview_template(template_name):
    """Preview template with sample data"""
    try:
        import os
        template_path = f'email_templates/{template_name}.html'
        full_path = os.path.join('app/templates', template_path)
        
        if not os.path.exists(full_path):
            return jsonify({'error': 'Template not found'}), 404
        
        with open(full_path, 'r') as f:
            html = f.read()
        
        # Sample data replacements
        replacements = {
            '{{first_name}}': 'John',
            '{{last_name}}': 'Doe',
            '{{email}}': 'john@example.com',
            '{{company}}': 'Acme Corp',
            '{{company_name}}': 'Acme Corp',
            '{{unsubscribe_url}}': '#',
            '{{action_url}}': '#'
        }
        
        for key, value in replacements.items():
            html = html.replace(key, value)
        
        return html, 200, {'Content-Type': 'text/html'}
        
    except Exception as e:
        logger.error(f"Preview error: {e}")
        return jsonify({'error': str(e)}), 500
