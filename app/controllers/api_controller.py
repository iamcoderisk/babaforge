from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from app import db
from app.models.contact import Contact
from app.models.email import Email
from app.models.campaign import Campaign
from app.models.domain import Domain
import csv
import io
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

api_bp = Blueprint('api', __name__, url_prefix='/api')

# Disable CSRF for API routes
@api_bp.before_request
def before_request():
    """Set up request context"""
    pass

@api_bp.route('/test', methods=['GET'])
def test():
    """Test API endpoint"""
    return jsonify({'success': True, 'message': 'API is working'})

@api_bp.route('/contacts/parse-csv', methods=['POST'])
@login_required
def parse_csv():
    """Parse CSV file and return contacts"""
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'No file uploaded'}), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected'}), 400
        
        # Read file content
        if file.filename.endswith('.csv'):
            # Read CSV
            stream = io.StringIO(file.stream.read().decode("UTF8"), newline=None)
            csv_reader = csv.DictReader(stream)
            contacts = list(csv_reader)
        elif file.filename.endswith(('.xlsx', '.xls')):
            # Read Excel
            try:
                import pandas as pd
                df = pd.read_excel(file)
                contacts = df.to_dict('records')
            except ImportError:
                return jsonify({'success': False, 'error': 'Excel support not available. Please use CSV format.'}), 400
        else:
            return jsonify({'success': False, 'error': 'Invalid file format. Use CSV or Excel'}), 400
        
        # Validate and clean contacts
        valid_contacts = []
        for row in contacts:
            # Normalize keys (handle different column names)
            email = row.get('email') or row.get('Email') or row.get('EMAIL')
            
            if email and '@' in str(email):
                contact = {
                    'email': str(email).strip(),
                    'first_name': str(row.get('first_name') or row.get('First Name') or row.get('firstname') or '').strip(),
                    'last_name': str(row.get('last_name') or row.get('Last Name') or row.get('lastname') or '').strip(),
                    'company': str(row.get('company') or row.get('Company') or row.get('COMPANY') or '').strip(),
                }
                valid_contacts.append(contact)
        
        if len(valid_contacts) == 0:
            return jsonify({
                'success': False,
                'error': 'No valid contacts found. Make sure your file has an "email" column.'
            }), 400
        
        return jsonify({
            'success': True,
            'contacts': valid_contacts,
            'total': len(valid_contacts)
        })
        
    except Exception as e:
        logger.error(f"Parse CSV error: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500

@api_bp.route('/contacts', methods=['POST'])
@login_required
def add_contact():
    """Add a new contact"""
    try:
        org = current_user.organization
        
        if not org:
            return jsonify({'success': False, 'error': 'Organization not found'}), 400
        
        data = request.get_json()
        
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        
        email = data.get('email', '').strip()
        
        if not email or '@' not in email:
            return jsonify({'success': False, 'error': 'Valid email is required'}), 400
        
        # Check if contact already exists
        existing = Contact.query.filter_by(
            organization_id=org.id,
            email=email
        ).first()
        
        if existing:
            return jsonify({'success': False, 'error': 'Contact already exists'}), 400
        
        # Create contact
        contact = Contact(organization_id=org.id)
        contact.email = email
        contact.first_name = data.get('first_name', '').strip()
        contact.last_name = data.get('last_name', '').strip()
        contact.company = data.get('company', '').strip()
        
        db.session.add(contact)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Contact added successfully',
            'contact': {'id': contact.id, 'email': contact.email}
        })
        
    except Exception as e:
        logger.error(f"Add contact error: {e}", exc_info=True)
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@api_bp.route('/contacts/import', methods=['POST'])
@login_required
def import_contacts():
    """Import contacts from CSV"""
    try:
        org = current_user.organization
        
        if not org:
            return jsonify({'success': False, 'error': 'Organization not found'}), 400
        
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'No file uploaded'}), 400
        
        file = request.files['file']
        
        # Parse CSV
        if file.filename.endswith('.csv'):
            stream = io.StringIO(file.stream.read().decode("UTF8"), newline=None)
            csv_reader = csv.DictReader(stream)
            rows = list(csv_reader)
        elif file.filename.endswith(('.xlsx', '.xls')):
            try:
                import pandas as pd
                df = pd.read_excel(file)
                rows = df.to_dict('records')
            except ImportError:
                return jsonify({'success': False, 'error': 'Excel support not available'}), 400
        else:
            return jsonify({'success': False, 'error': 'Invalid file format'}), 400
        
        imported = 0
        skipped = 0
        
        for row in rows:
            email = str(row.get('email') or row.get('Email') or '').strip()
            
            if not email or '@' not in email:
                skipped += 1
                continue
            
            # Check if exists
            existing = Contact.query.filter_by(
                organization_id=org.id,
                email=email
            ).first()
            
            if existing:
                skipped += 1
                continue
            
            # Create contact
            contact = Contact(organization_id=org.id)
            contact.email = email
            contact.first_name = str(row.get('first_name') or row.get('First Name') or '').strip()
            contact.last_name = str(row.get('last_name') or row.get('Last Name') or '').strip()
            contact.company = str(row.get('company') or row.get('Company') or '').strip()
            
            db.session.add(contact)
            imported += 1
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'imported': imported,
            'skipped': skipped,
            'message': f'Imported {imported} contacts, skipped {skipped}'
        })
        
    except Exception as e:
        logger.error(f"Import contacts error: {e}", exc_info=True)
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@api_bp.route('/contacts/<contact_id>', methods=['DELETE'])
@login_required
def delete_contact(contact_id):
    """Delete a contact"""
    try:
        org = current_user.organization
        
        if not org:
            return jsonify({'success': False, 'error': 'Organization not found'}), 400
        
        contact = Contact.query.filter_by(
            id=contact_id,
            organization_id=org.id
        ).first()
        
        if not contact:
            return jsonify({'success': False, 'error': 'Contact not found'}), 404
        
        db.session.delete(contact)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Contact deleted successfully'
        })
        
    except Exception as e:
        logger.error(f"Delete contact error: {e}", exc_info=True)
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@api_bp.route('/emails/send', methods=['POST'])
@login_required
def send_single_email():
    """Send a single email"""
    try:
        org = current_user.organization
        
        if not org:
            return jsonify({'success': False, 'error': 'Organization not found'}), 400
        
        # Get form data
        from_name = request.form.get('from_name', '').strip()
        from_domain = request.form.get('from_domain', '').strip()
        to_email = request.form.get('to_email', '').strip()
        subject = request.form.get('subject', '').strip()
        html_body = request.form.get('html_body', '').strip()
        text_body = request.form.get('text_body', '').strip()
        priority = request.form.get('priority', '5')
        is_test = request.form.get('is_test', 'false') == 'true'
        
        logger.info(f"Send email request - to: {to_email}, subject: {subject}, is_test: {is_test}")
        
        if not to_email or not subject:
            return jsonify({'success': False, 'error': 'Missing required fields: to_email and subject'}), 400
        
        if not html_body and not text_body:
            return jsonify({'success': False, 'error': 'Email body is required (html_body or text_body)'}), 400
        
        # Verify domain
        domain = Domain.query.filter_by(
            organization_id=org.id,
            domain_name=from_domain,
            dns_verified=True
        ).first()
        
        if not domain:
            return jsonify({'success': False, 'error': f'Domain {from_domain} is not verified'}), 400
        
        # Create from email
        from_email = f"{from_name}@{from_domain}" if from_name else f"noreply@{from_domain}"
        
        # Create email record
        email = Email(
            organization_id=org.id,
            from_email=from_email,
            to_email=to_email
        )
        email.subject = subject
        email.html_body = html_body if html_body else None
        email.text_body = text_body if text_body else None
        email.status = 'queued'
        
        db.session.add(email)
        db.session.commit()
        
        logger.info(f"Email queued successfully - ID: {email.id}")
        
        return jsonify({
            'success': True,
            'message': 'Email queued successfully' if not is_test else 'Test email sent successfully',
            'email_id': email.id
        })
        
    except Exception as e:
        logger.error(f"Send email error: {e}", exc_info=True)
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@api_bp.route('/campaigns/bulk-send', methods=['POST'])
@login_required
def bulk_send():
    """Send bulk email campaign"""
    try:
        org = current_user.organization
        
        if not org:
            return jsonify({'success': False, 'error': 'Organization not found'}), 400
        
        # Get form data
        contacts_json = request.form.get('contacts')
        subject = request.form.get('subject')
        html_body = request.form.get('html_body')
        from_name = request.form.get('from_name', '')
        from_domain = request.form.get('from_domain')
        send_option = request.form.get('send_option', 'now')
        
        if not contacts_json or not subject or not html_body:
            return jsonify({'success': False, 'error': 'Missing required fields'}), 400
        
        # Parse contacts
        import json
        contacts = json.loads(contacts_json)
        
        if len(contacts) == 0:
            return jsonify({'success': False, 'error': 'No contacts provided'}), 400
        
        # Verify domain
        domain = Domain.query.filter_by(
            organization_id=org.id,
            domain_name=from_domain,
            dns_verified=True
        ).first()
        
        if not domain:
            return jsonify({'success': False, 'error': f'Domain {from_domain} is not verified'}), 400
        
        # Create campaign
        campaign = Campaign(organization_id=org.id)
        campaign.name = f"Bulk Campaign - {datetime.utcnow().strftime('%Y-%m-%d %H:%M')}"
        campaign.subject = subject
        campaign.html_body = html_body
        campaign.status = 'queued' if send_option == 'now' else 'scheduled'
        campaign.total_recipients = len(contacts)
        
        if send_option == 'schedule':
            schedule_time = request.form.get('schedule_time')
            if schedule_time:
                campaign.scheduled_at = datetime.fromisoformat(schedule_time)
        
        db.session.add(campaign)
        db.session.flush()
        
        # Create email records
        from_email = f"{from_name}@{from_domain}" if from_name else f"noreply@{from_domain}"
        
        queued_count = 0
        for contact in contacts:
            # Replace variables in subject and body
            personalized_subject = subject
            personalized_body = html_body
            
            for key, value in contact.items():
                personalized_subject = personalized_subject.replace(f"{{{{{key}}}}}", str(value))
                personalized_body = personalized_body.replace(f"{{{{{key}}}}}", str(value))
            
            # Create email
            email = Email(
                organization_id=org.id,
                from_email=from_email,
                to_email=contact['email']
            )
            email.subject = personalized_subject
            email.html_body = personalized_body
            email.campaign_id = campaign.id
            email.status = 'queued'
            
            db.session.add(email)
            queued_count += 1
        
        campaign.emails_sent = 0
        db.session.commit()
        
        logger.info(f"Bulk campaign created - ID: {campaign.id}, emails: {queued_count}")
        
        return jsonify({
            'success': True,
            'message': f'Campaign created with {queued_count} emails',
            'campaign_id': campaign.id,
            'total': queued_count
        })
        
    except Exception as e:
        logger.error(f"Bulk send error: {e}", exc_info=True)
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@api_bp.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({'success': False, 'error': 'Endpoint not found'}), 404

@api_bp.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    logger.error(f"Internal error: {error}")
    return jsonify({'success': False, 'error': 'Internal server error'}), 500
