from flask import Blueprint, render_template, request, redirect, url_for, jsonify
from flask_login import login_required, current_user
from app import db
from sqlalchemy import text
import logging

logger = logging.getLogger(__name__)

contact_bp = Blueprint('contact', __name__)

@contact_bp.route('/contacts')
@contact_bp.route('/dashboard/contacts')
@login_required
def list_contacts():
    """List all contacts"""
    try:
        result = db.session.execute(
            text("""
                SELECT id, email, first_name, last_name, company, created_at 
                FROM contacts 
                WHERE organization_id = :org_id 
                ORDER BY created_at DESC
            """),
            {'org_id': current_user.organization_id}
        )
        
        contacts = []
        for row in result:
            contacts.append({
                'id': row[0],
                'email': row[1],
                'first_name': row[2] or '',
                'last_name': row[3] or '',
                'company': row[4],
                'created_at': row[5]
            })
        
        return render_template('dashboard/contacts/list.html', contacts=contacts)
    except Exception as e:
        logger.error(f"List contacts error: {e}", exc_info=True)
        return render_template('dashboard/contacts/list.html', contacts=[])

@contact_bp.route('/contacts/import')
@contact_bp.route('/dashboard/contacts/import')
@login_required
def import_contacts():
    """Import contacts page"""
    return render_template('dashboard/contacts/import.html')

@contact_bp.route('/contacts/add')
@contact_bp.route('/dashboard/contacts/add')
@login_required
def add_contact():
    """Add single contact page"""
    return render_template('dashboard/contacts/add.html')
