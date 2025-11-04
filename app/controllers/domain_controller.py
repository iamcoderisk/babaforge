from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app import db
from app.models.domain import Domain

domain_bp = Blueprint('domains', __name__)

@domain_bp.route('/domains')
@domain_bp.route('/dashboard/domains')
@login_required
def list_domains():
    domains = Domain.query.filter_by(organization_id=current_user.organization_id).all()
    return render_template('dashboard/domains.html', domains=domains)

@domain_bp.route('/domains/add')
@domain_bp.route('/dashboard/domains/add')
@login_required
def add_domain():
    return render_template('dashboard/domains/add.html')

@domain_bp.route('/domains/<domain_id>')
@domain_bp.route('/dashboard/domains/<domain_id>')
@login_required
def view_domain(domain_id):
    domain = Domain.query.get_or_404(domain_id)
    return render_template('dashboard/domains/view.html', domain=domain)
