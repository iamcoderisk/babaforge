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
        contact = Contact(organization_id=org.id, email=email)
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
            contact = Contact(organization_id=org.id, email=email)
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
        # Create email record
        email = Email(
            organization_id=org.id,
            sender=from_email,
            recipient=to_email,
            subject=subject,
            html_body=html_body if html_body else None,
            text_body=text_body if text_body else None,
            status="queued"
        )
        
        db.session.add(email)
        db.session.commit()
        
        # Queue email for sending via Redis
        try:
            import redis
            import json
            redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True)
            
            email_data = {
                'id': str(email.id),
                'from': from_email,
                'to': to_email,
                'subject': subject,
                'html': html_body or text_body,
                'text': text_body,
                'priority': int(priority) if priority else 5
            }
            
            queue_name = f'outgoing_{email_data["priority"]}'
            redis_client.lpush(queue_name, json.dumps(email_data))
            logger.info(f"✅ Email {email.id} queued to {queue_name}")
        except Exception as e:
            logger.error(f"❌ Failed to queue email: {e}")
        
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
        
        # Get form data
        campaign_name = request.form.get('campaign_name')
        subject = request.form.get('subject')
        body = request.form.get('body')
        from_name = request.form.get('from_name')
        from_domain = request.form.get('from_domain')
        
        # Validate required fields
        if not all([campaign_name, subject, body, from_name, from_domain]):
            return jsonify({
                'success': False,
                'error': 'Missing required fields: campaign_name, subject, body, from_name, from_domain'
            })
        
        sender_email = f"{from_name}@{from_domain}"
        
        # Get recipients
        contact_ids = request.form.get('contact_ids')
        uploaded_contacts = request.form.get('uploaded_contacts')
        
        recipients = []
        
        if contact_ids:
            # Use existing contacts
            import json
            contact_id_list = json.loads(contact_ids)
            from app.models.contact import Contact
            
            for contact_id in contact_id_list:
                contact = Contact.query.filter_by(
                    id=contact_id,
                    organization_id=org.id
                ).first()
                
                if contact:
                    recipients.append({
                        'email': contact.email,
                        'first_name': contact.first_name or contact.name or '',
                        'last_name': contact.last_name or '',
                        'company': contact.company or ''
                    })
        
        elif uploaded_contacts:
            # Use uploaded contacts
            import json
            recipients = json.loads(uploaded_contacts)
        
        if not recipients:
            return jsonify({
                'success': False,
                'error': 'No recipients selected'
            })
        
        # Create campaign
        from app.models.campaign import Campaign
        campaign = Campaign(
            organization_id=org.id,
            name=campaign_name,
            subject=subject,
            html_body=body,
            status='sending',
            total_recipients=len(recipients)
        )
        db.session.add(campaign)
        db.session.flush()
        
        # Create email records and queue
        import redis
        redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True)
        
        queued_count = 0
        for recipient in recipients:
            # Personalize content
            personalized_subject = subject
            personalized_body = body
            
            for key, value in recipient.items():
                personalized_subject = personalized_subject.replace(f'{{{{{key}}}}}', str(value))
                personalized_body = personalized_body.replace(f'{{{{{key}}}}}', str(value))
            
            # Create email record
            from app.models.email import Email
            email_record = Email(
                organization_id=org.id,
                campaign_id=campaign.id,
                sender=sender_email,
                recipient=recipient['email'],
                subject=personalized_subject,
                html_body=personalized_body,
                status='queued'
            )
            db.session.add(email_record)
            db.session.flush()
            
            # Queue email
            email_data = {
                'id': str(email_record.id),
                'from': sender_email,
                'to': recipient['email'],
                'subject': personalized_subject,
                'html_body': personalized_body,
                'campaign_id': str(campaign.id),
                'retry_count': 0
            }
            
            import json
            redis_client.lpush('outgoing_10', json.dumps(email_data))
            queued_count += 1
        
        db.session.commit()
        
        logger.info(f"Campaign {campaign_name} queued with {queued_count} emails")
        
        return jsonify({
            'success': True,
            'message': f'Campaign queued successfully! Sending to {queued_count} recipients.',
            'campaign_id': campaign.id,
            'queued': queued_count
        })
    
    except Exception as e:
        logger.error(f"Bulk send error: {e}", exc_info=True)
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        })

@api_bp.route('/v1/send', methods=['POST'])
def send_email_api():
    """Public API endpoint to send emails"""
    try:
        # Get JSON data
        data = request.get_json()
        
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        
        # Required fields
        to_email = data.get('to', '').strip()
        from_email = data.get('from', '').strip()
        subject = data.get('subject', '').strip()
        html_body = data.get('html_body', '').strip()
        text_body = data.get('text_body', '').strip()
        
        if not to_email or not from_email or not subject:
            return jsonify({'success': False, 'error': 'Missing required fields: to, from, subject'}), 400
        
        if not html_body and not text_body:
            return jsonify({'success': False, 'error': 'Email body is required (html_body or text_body)'}), 400
        
        # Extract domain from from_email
        from_domain = from_email.split('@')[1] if '@' in from_email else None
        
        if not from_domain:
            return jsonify({'success': False, 'error': 'Invalid from email address'}), 400
        
        # Verify domain exists (no org check for public API)
        domain = Domain.query.filter_by(
            domain_name=from_domain,
            dns_verified=True
        ).first()
        
        if not domain:
            return jsonify({'success': False, 'error': f'Domain {from_domain} is not verified'}), 400
        
        # Create email record
        email = Email(
            organization_id=domain.organization_id,
            sender=from_email,
            recipient=to_email,
            subject=subject,
            html_body=html_body if html_body else None,
            text_body=text_body if text_body else None,
            status="queued"
        )
        
        db.session.add(email)
        db.session.commit()
        
        # Queue email for sending via Redis
        try:
            import redis
            import json
            redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True)
            
            email_data = {
                'id': str(email.id),
                'from': from_email,
                'to': to_email,
                'subject': subject,
                'html': html_body or text_body,
                'text': text_body,
                'priority': 5
            }
            
            queue_name = 'outgoing_5'
            redis_client.lpush(queue_name, json.dumps(email_data))
            logger.info(f"✅ API Email {email.id} queued to {queue_name}")
        except Exception as e:
            logger.error(f"❌ Failed to queue email: {e}")
        
        return jsonify({
            'success': True,
            'message': 'Email queued successfully',
            'email_id': email.id
        }), 200
        
    except Exception as e:
        logger.error(f"API send email error: {e}", exc_info=True)
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

        # Create email records and queue them
        from_email = f"{from_name}@{from_domain}" if from_name else f"noreply@{from_domain}"
        
        import redis
        redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True)
        
        queued_count = 0
        for contact in contacts:
            try:
                # Replace variables in subject and body
                personalized_subject = subject
                personalized_body = html_body
                
                for key, value in contact.items():
                    placeholder = f"{{{{{key}}}}}"
                    personalized_subject = personalized_subject.replace(placeholder, str(value))
                    personalized_body = personalized_body.replace(placeholder, str(value))
                
                # Create email record
                email = Email(
                    organization_id=org.id,
                    sender=from_email,
                    recipient=contact['email'],
                    subject=personalized_subject
                )
                email.html_body = personalized_body
                email.status = 'queued' 
                
                db.session.add(email)
                db.session.flush()
                
                # Queue email for worker
                email_data = {
                    'id': str(email.id),
                    'from': from_email,
                    'to': contact['email'],
                    'subject': personalized_subject,
                    'html': personalized_body,
                    'priority': 5
                }
                
                redis_client.lpush('outgoing_5', json.dumps(email_data))
                queued_count += 1
                
            except Exception as e:
                logger.error(f"Error queuing email for {contact.get('email')}: {e}")
                continue
        
        campaign.emails_sent = 0
        db.session.commit()
        
        logger.info(f"Bulk campaign created - ID: {campaign.id}, emails: {queued_count}")
        
        return jsonify({
            'success': True,
            'message': f'Campaign created! {queued_count} emails queued for sending',
            'campaign_id': campaign.id,
            'total': queued_count
        })
        
    except Exception as e:
        logger.error(f"Bulk send error: {e}", exc_info=True)
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@api_bp.route('/settings/generate-api-key', methods=['POST'])
@login_required
def generate_api_key():
    """Generate new API key for organization"""
    try:
        org = current_user.organization
        
        # Generate a new API key
        import secrets
        api_key = f"sk_live_{secrets.token_urlsafe(32)}"
        
        # Store it in the organization (you may want to hash this)
        org.api_key = api_key
        db.session.commit()
        
        logger.info(f"Generated new API key for org {org.id}")
        
        return jsonify({
            'success': True,
            'api_key': api_key
        })
    
    except Exception as e:
        logger.error(f"Error generating API key: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api_bp.route('/templates', methods=['GET'])
@login_required
def get_templates():
    """Get all templates"""
    try:
        from app.models.email_template import EmailTemplate
        org = current_user.organization
        
        templates = EmailTemplate.query.filter(
            (EmailTemplate.organization_id == org.id) | (EmailTemplate.is_system == True)
        ).all()
        
        return jsonify({
            'success': True,
            'templates': [{
                'id': t.id,
                'name': t.name,
                'category': t.category,
                'thumbnail': t.thumbnail,
                'is_system': t.is_system
            } for t in templates]
        })
    except Exception as e:
        logger.error(f"Error getting templates: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@api_bp.route('/templates', methods=['POST'])
@login_required
def create_template():
    """Create new template"""
    try:
        from app.models.email_template import EmailTemplate
        org = current_user.organization
        
        data = request.get_json()
        
        template = EmailTemplate(
            organization_id=org.id,
            name=data.get('name', 'Untitled'),
            category=data.get('category'),
            html_content=data.get('html_content'),
            json_structure=data.get('json_structure')
        )
        
        db.session.add(template)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'template_id': template.id
        })
    except Exception as e:
        logger.error(f"Error creating template: {e}")
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@api_bp.route('/templates/<int:template_id>', methods=['GET'])
@login_required
def get_template(template_id):
    """Get template by ID"""
    try:
        from app.models.email_template import EmailTemplate
        org = current_user.organization
        
        template = EmailTemplate.query.filter_by(id=template_id).first()
        
        if not template:
            return jsonify({'success': False, 'error': 'Template not found'}), 404
            
        if template.organization_id != org.id and not template.is_system:
            return jsonify({'success': False, 'error': 'Unauthorized'}), 403
        
        return jsonify({
            'success': True,
            'template': {
                'id': template.id,
                'name': template.name,
                'html_content': template.html_content,
                'json_structure': template.json_structure
            }
        })
    except Exception as e:
        logger.error(f"Error getting template: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@api_bp.route('/upload/image', methods=['POST'])
@login_required
def upload_image():
    """Upload image for email builder"""
    try:
        if 'files' not in request.files:
            return jsonify({'success': False, 'error': 'No file provided'}), 400
        
        file = request.files['files']
        
        if file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected'}), 400
        
        # Save file
        import os
        from werkzeug.utils import secure_filename
        
        upload_folder = '/opt/sendbaba-smtp/app/static/uploads'
        os.makedirs(upload_folder, exist_ok=True)
        
        filename = secure_filename(file.filename)
        filepath = os.path.join(upload_folder, filename)
        file.save(filepath)
        
        # Return URL
        url = f'/static/uploads/{filename}'
        
        return jsonify({
            'success': True,
            'data': [url]
        })
    except Exception as e:
        logger.error(f"Error uploading image: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500
