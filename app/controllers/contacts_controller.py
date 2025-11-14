from flask import Blueprint, render_template, request, jsonify, redirect, url_for
from flask_login import login_required, current_user
from app import db
from sqlalchemy import text
import logging
import pandas as pd
import io

logger = logging.getLogger(__name__)

contacts_bp = Blueprint('contacts', __name__, url_prefix='/dashboard/contacts')

@contacts_bp.route('/')
@login_required
def list_contacts():
    """List all contacts"""
    try:
        result = db.session.execute(
            text("SELECT id, email, first_name, last_name, company, created_at FROM contacts WHERE organization_id = :org_id ORDER BY created_at DESC"),
            {'org_id': current_user.organization_id}
        )
        
        contacts = []
        for row in result:
            contacts.append({
                'id': row[0],
                'email': row[1],
                'first_name': row[2],
                'last_name': row[3],
                'company': row[4],
                'created_at': row[5]
            })
        
        return render_template('dashboard/contacts/list.html', contacts=contacts)
    except Exception as e:
        logger.error(f"List contacts error: {e}", exc_info=True)
        return render_template('dashboard/contacts/list.html', contacts=[])

@contacts_bp.route('/import')
@login_required
def import_page():
    """Import contacts page"""
    return render_template('dashboard/contacts/import.html')

# API Endpoints
contacts_api_bp = Blueprint('contacts_api', __name__, url_prefix='/api/contacts')

@contacts_api_bp.route('/parse', methods=['POST'])
@login_required
def parse_file():
    """Parse uploaded CSV/Excel file"""
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'No file uploaded'}), 400
        
        file = request.files['file']
        
        # Read file
        if file.filename.endswith('.csv'):
            df = pd.read_csv(file)
        elif file.filename.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(file)
        else:
            return jsonify({'success': False, 'error': 'Unsupported file format'}), 400
        
        # Convert to dict
        headers = df.columns.tolist()
        rows = df.to_dict('records')
        
        return jsonify({
            'success': True,
            'headers': headers,
            'rows': rows,
            'total': len(rows)
        })
        
    except Exception as e:
        logger.error(f"Parse file error: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500

@contacts_api_bp.route('/import', methods=['POST'])
@login_required
def import_contacts():
    """Import contacts with mapping"""
    try:
        data = request.json
        rows = data.get('data', [])
        mapping = data.get('mapping', {})
        options = data.get('options', {})
        
        imported = 0
        skipped = 0
        
        for row in rows:
            email = row.get(mapping['email'], '').strip()
            
            if not email:
                skipped += 1
                continue
            
            # Validate email
            if options.get('validate_emails') and '@' not in email:
                skipped += 1
                continue
            
            # Check duplicates
            if options.get('skip_duplicates'):
                exists = db.session.execute(
                    text("SELECT COUNT(*) FROM contacts WHERE organization_id = :org_id AND email = :email"),
                    {'org_id': current_user.organization_id, 'email': email}
                ).scalar()
                
                if exists > 0:
                    skipped += 1
                    continue
            
            # Import contact
            first_name = row.get(mapping.get('first_name'), '') if mapping.get('first_name') else ''
            last_name = row.get(mapping.get('last_name'), '') if mapping.get('last_name') else ''
            company = row.get(mapping.get('company'), '') if mapping.get('company') else ''
            
            db.session.execute(
                text("""
                    INSERT INTO contacts (organization_id, email, first_name, last_name, company, created_at)
                    VALUES (:org_id, :email, :first_name, :last_name, :company, NOW())
                """),
                {
                    'org_id': current_user.organization_id,
                    'email': email,
                    'first_name': first_name,
                    'last_name': last_name,
                    'company': company
                }
            )
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
