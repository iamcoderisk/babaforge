from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app import db
from app.models.contact import Contact

contact_bp = Blueprint('contacts', __name__)

@contact_bp.route('/contacts')
@contact_bp.route('/dashboard/contacts')
@login_required
def list_contacts():
    contacts = Contact.query.filter_by(organization_id=current_user.organization_id).all()
    return render_template('dashboard/contacts.html', contacts=contacts)

@contact_bp.route('/contacts/add')
@contact_bp.route('/dashboard/contacts/add')
@login_required
def add_contact():
    return render_template('dashboard/contacts/add.html')

@contact_bp.route('/contacts/<contact_id>')
@contact_bp.route('/dashboard/contacts/<contact_id>')
@login_required
def view_contact(contact_id):
    contact = Contact.query.get_or_404(contact_id)
    return render_template('dashboard/contacts/view.html', contact=contact)
