from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user
from app import db
from app.models.contact import Contact, ContactList, BulkImport
from app.middleware.auth import require_api_key
from datetime import datetime
import csv
import io
import logging

logger = logging.getLogger(__name__)

contact_bp = Blueprint('contacts', __name__)

# ============= API Endpoints (with API key) =============

@contact_bp.route('/contact', methods=['POST'])
@require_api_key
def create_contact():
    """Create a single contact"""
    try:
        data = request.get_json()
        
        email = data.get('email', '').strip().lower()
        if not email:
            return jsonify({'success': False, 'error': 'Email is required'}), 400
        
        # Check for duplicate
        existing = Contact.query.filter_by(
            organization_id=request.organization.id,
            email=email
        ).first()
        
        if existing:
            return jsonify({
                'success': False,
                'error': 'Contact with this email already exists',
                'contact_id': existing.id
            }), 400
        
        # Create contact
        contact = Contact(
            organization_id=request.organization.id,
            email=email,
            first_name=data.get('first_name'),
            last_name=data.get('last_name'),
            phone=data.get('phone'),
            company=data.get('company'),
            custom_fields=data.get('custom_fields'),
            tags=data.get('tags', [])
        )
        
        db.session.add(contact)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'contact': contact.to_dict(),
            'message': 'Contact created successfully'
        }), 201
        
    except Exception as e:
        logger.error(f"Create contact error: {e}")
        db.session.rollback()
        return jsonify({'success': False, 'error': 'Failed to create contact'}), 500

@contact_bp.route('/contacts', methods=['GET'])
@require_api_key
def list_contacts():
    """List all contacts with pagination"""
    try:
        page = int(request.args.get('page', 1))
        per_page = min(int(request.args.get('per_page', 50)), 100)
        status = request.args.get('status', 'active')
        search = request.args.get('search', '').strip()
        
        query = Contact.query.filter_by(
            organization_id=request.organization.id
        )
        
        if status:
            query = query.filter_by(status=status)
        
        if search:
            query = query.filter(
                db.or_(
                    Contact.email.ilike(f'%{search}%'),
                    Contact.first_name.ilike(f'%{search}%'),
                    Contact.last_name.ilike(f'%{search}%'),
                    Contact.company.ilike(f'%{search}%')
                )
            )
        
        pagination = query.order_by(Contact.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            'success': True,
            'contacts': [c.to_dict() for c in pagination.items],
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': pagination.total,
                'pages': pagination.pages,
                'has_next': pagination.has_next,
                'has_prev': pagination.has_prev
            }
        })
        
    except Exception as e:
        logger.error(f"List contacts error: {e}")
        return jsonify({'success': False, 'error': 'Failed to list contacts'}), 500

@contact_bp.route('/contact/<contact_id>', methods=['GET'])
@require_api_key
def get_contact(contact_id):
    """Get a single contact"""
    try:
        contact = Contact.query.filter_by(
            id=contact_id,
            organization_id=request.organization.id
        ).first()
        
        if not contact:
            return jsonify({'success': False, 'error': 'Contact not found'}), 404
        
        return jsonify({
            'success': True,
            'contact': contact.to_dict()
        })
        
    except Exception as e:
        logger.error(f"Get contact error: {e}")
        return jsonify({'success': False, 'error': 'Failed to get contact'}), 500

@contact_bp.route('/contact/<contact_id>', methods=['PUT'])
@require_api_key
def update_contact(contact_id):
    """Update a contact"""
    try:
        contact = Contact.query.filter_by(
            id=contact_id,
            organization_id=request.organization.id
        ).first()
        
        if not contact:
            return jsonify({'success': False, 'error': 'Contact not found'}), 404
        
        data = request.get_json()
        
        # Update fields
        if 'first_name' in data:
            contact.first_name = data['first_name']
        if 'last_name' in data:
            contact.last_name = data['last_name']
        if 'phone' in data:
            contact.phone = data['phone']
        if 'company' in data:
            contact.company = data['company']
        if 'custom_fields' in data:
            contact.custom_fields = data['custom_fields']
        if 'tags' in data:
            contact.tags = data['tags']
        if 'status' in data:
            contact.status = data['status']
        
        contact.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'contact': contact.to_dict(),
            'message': 'Contact updated successfully'
        })
        
    except Exception as e:
        logger.error(f"Update contact error: {e}")
        db.session.rollback()
        return jsonify({'success': False, 'error': 'Failed to update contact'}), 500

@contact_bp.route('/contact/<contact_id>', methods=['DELETE'])
@require_api_key
def delete_contact(contact_id):
    """Delete a contact"""
    try:
        contact = Contact.query.filter_by(
            id=contact_id,
            organization_id=request.organization.id
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
        logger.error(f"Delete contact error: {e}")
        db.session.rollback()
        return jsonify({'success': False, 'error': 'Failed to delete contact'}), 500

@contact_bp.route('/contacts/bulk', methods=['POST'])
@require_api_key
def bulk_import():
    """Bulk import contacts from CSV"""
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'No file provided'}), 400
        
        file = request.files['file']
        
        if not file.filename.endswith('.csv'):
            return jsonify({'success': False, 'error': 'Only CSV files are supported'}), 400
        
        # Create import record
        import_record = BulkImport(
            organization_id=request.organization.id,
            filename=file.filename
        )
        db.session.add(import_record)
        db.session.flush()
        
        # Read CSV
        stream = io.StringIO(file.stream.read().decode("UTF8"), newline=None)
        csv_reader = csv.DictReader(stream)
        
        total_rows = 0
        successful = 0
        failed = 0
        duplicates = 0
        errors = []
        
        for row_num, row in enumerate(csv_reader, start=2):
            total_rows += 1
            
            try:
                email = row.get('email', '').strip().lower()
                
                if not email:
                    failed += 1
                    errors.append({'row': row_num, 'error': 'Missing email'})
                    continue
                
                # Check for duplicate
                existing = Contact.query.filter_by(
                    organization_id=request.organization.id,
                    email=email
                ).first()
                
                if existing:
                    duplicates += 1
                    continue
                
                # Create contact
                contact = Contact(
                    organization_id=request.organization.id,
                    email=email,
                    first_name=row.get('first_name', '').strip() or None,
                    last_name=row.get('last_name', '').strip() or None,
                    phone=row.get('phone', '').strip() or None,
                    company=row.get('company', '').strip() or None
                )
                
                db.session.add(contact)
                successful += 1
                
                # Commit in batches of 100
                if successful % 100 == 0:
                    db.session.commit()
                
            except Exception as e:
                failed += 1
                errors.append({'row': row_num, 'error': str(e)})
                continue
        
        # Final commit
        db.session.commit()
        
        # Update import record
        import_record.status = 'completed'
        import_record.total_rows = total_rows
        import_record.processed_rows = total_rows
        import_record.successful_imports = successful
        import_record.failed_imports = failed
        import_record.duplicate_emails = duplicates
        import_record.errors = errors[:100]  # Store first 100 errors
        import_record.completed_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'import_id': import_record.id,
            'summary': {
                'total_rows': total_rows,
                'successful': successful,
                'failed': failed,
                'duplicates': duplicates
            },
            'errors': errors[:10],  # Return first 10 errors
            'message': f'Imported {successful} contacts successfully'
        }), 201
        
    except Exception as e:
        logger.error(f"Bulk import error: {e}")
        db.session.rollback()
        return jsonify({'success': False, 'error': 'Failed to import contacts'}), 500

@contact_bp.route('/contacts/stats', methods=['GET'])
@require_api_key
def get_stats():
    """Get contact statistics"""
    try:
        total = Contact.query.filter_by(
            organization_id=request.organization.id
        ).count()
        
        active = Contact.query.filter_by(
            organization_id=request.organization.id,
            status='active'
        ).count()
        
        unsubscribed = Contact.query.filter_by(
            organization_id=request.organization.id,
            status='unsubscribed'
        ).count()
        
        bounced = Contact.query.filter_by(
            organization_id=request.organization.id,
            status='bounced'
        ).count()
        
        return jsonify({
            'success': True,
            'stats': {
                'total': total,
                'active': active,
                'unsubscribed': unsubscribed,
                'bounced': bounced
            }
        })
        
    except Exception as e:
        logger.error(f"Get stats error: {e}")
        return jsonify({'success': False, 'error': 'Failed to get stats'}), 500
