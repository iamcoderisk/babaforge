from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app import db
from app.models.contact_list import ContactList
from app.models.contact import Contact
from app.models.campaign import Campaign
from datetime import datetime

bulk_send_bp = Blueprint('bulk_send', __name__)

@bulk_send_bp.route('/bulk-send', methods=['GET'])
@login_required
def index():
    """Bulk send email"""
    contact_lists = ContactList.query.filter_by(
        organization_id=current_user.organization_id
    ).all()
    return render_template('dashboard/bulk-send.html', contact_lists=contact_lists)

@bulk_send_bp.route('/bulk-send/send', methods=['POST'])
@login_required
def send():
    """Send bulk email"""
    try:
        list_ids = request.form.getlist('list_ids[]')
        subject = request.form.get('subject')
        html_content = request.form.get('html_content')
        
        contacts = Contact.query.filter(
            Contact.list_id.in_(list_ids),
            Contact.status == 'active'
        ).all()
        
        from app.services.email_service import send_email
        
        sent = 0
        for contact in contacts:
            try:
                send_email(contact.email, subject, html_content)
                sent += 1
            except:
                pass
        
        flash(f'Sent to {sent} contacts!', 'success')
        return redirect(url_for('dashboard.index'))
    except Exception as e:
        flash(str(e), 'danger')
        return redirect(url_for('bulk_send.index'))
