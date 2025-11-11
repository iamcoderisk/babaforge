from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from app import db, redis_client
from sqlalchemy import text
import json
import uuid
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

api_bp = Blueprint('api', __name__, url_prefix='/api')

@api_bp.route('/emails/send', methods=['POST'])
@login_required
def send_email():
    """Send email and track in database"""
    try:
        # Get form data
        from_name = request.form.get('from_name', 'noreply')
        from_domain = request.form.get('from_domain')
        to_email = request.form.get('to_email')
        subject = request.form.get('subject')
        html_body = request.form.get('html_body', '')
        is_test = request.form.get('is_test', 'false').lower() == 'true'
        
        if not to_email or not subject:
            return jsonify({'success': False, 'error': 'Missing required fields'}), 400
        
        # Build from email
        from_email = f"{from_name}@{from_domain}" if from_domain else f"{from_name}@sendbaba.com"
        
        # Generate email ID
        email_id = str(uuid.uuid4())
        
        # Create campaign if not a test
        campaign_id = None
        if not is_test:
            campaign_id = str(uuid.uuid4())
            
            # Insert campaign
            db.session.execute(
                text("""
                    INSERT INTO campaigns (
                        id, organization_id, name, subject, from_email,
                        status, emails_sent, sent_count, total_recipients,
                        created_at, started_at
                    )
                    VALUES (
                        :id, :org_id, :name, :subject, :from_email,
                        'sending', 0, 0, 1, NOW(), NOW()
                    )
                """),
                {
                    'id': campaign_id,
                    'org_id': current_user.organization_id,
                    'name': f'Email to {to_email}',
                    'subject': subject,
                    'from_email': from_email
                }
            )
        
        # Save to emails table
        db.session.execute(
            text("""
                INSERT INTO emails (
                    id, organization_id, campaign_id, from_email, to_email,
                    subject, html_body, status, created_at
                )
                VALUES (
                    :id, :org_id, :campaign_id, :from_email, :to_email,
                    :subject, :html_body, 'queued', NOW()
                )
            """),
            {
                'id': email_id,
                'org_id': current_user.organization_id,
                'campaign_id': campaign_id,
                'from_email': from_email,
                'to_email': to_email,
                'subject': subject,
                'html_body': html_body
            }
        )
        
        # Queue email for sending
        email_data = {
            'id': email_id,
            'campaign_id': campaign_id,
            'org_id': current_user.organization_id,
            'from': from_email,
            'to': to_email,
            'subject': subject,
            'html_body': html_body,
            'text_body': '',
            'priority': 10
        }
        
        if redis_client:
            redis_client.lpush('outgoing_10', json.dumps(email_data))
            logger.info(f"Email {email_id} queued for {to_email}")
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'email_id': email_id,
            'campaign_id': campaign_id,
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
            return jsonify({'success': False, 'error': 'No file uploaded'}), 400
        
        file = request.files['file']
        if not file.filename.endswith('.csv'):
            return jsonify({'success': False, 'error': 'Only CSV files allowed'}), 400
        
        # Process CSV
        import csv
        import io
        
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
                    {
                        'id': contact_id,
                        'org_id': current_user.organization_id,
                        'email': email,
                        'name': name
                    }
                )
                imported += 1
            except:
                continue
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'imported': imported,
            'message': f'{imported} contacts imported'
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Import error: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500

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
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
