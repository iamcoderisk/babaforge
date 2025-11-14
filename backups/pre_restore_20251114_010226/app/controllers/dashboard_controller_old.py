from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app import db
from app.models.domain import Domain
from app.models.organization import Organization
from app.models.email import Email
from sqlalchemy import func
from datetime import datetime, timedelta

dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/dashboard')

@dashboard_bp.route('/')
@login_required
def index():
    """Main dashboard"""
    try:
        # Get organization
        org = current_user.organization
        
        if not org:
            flash('Organization not found. Please contact support.', 'danger')
            return redirect(url_for('web.index'))
        
        # Get domains
        domains = Domain.query.filter_by(
            organization_id=org.id
        ).order_by(Domain.created_at.desc()).all()
        
        verified_domains = [d for d in domains if d.dns_verified]
        
        # Get email stats (if Email model exists)
        try:
            today = datetime.utcnow().date()
            month_start = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            
            emails_today = Email.query.filter(
                Email.organization_id == org.id,
                func.date(Email.created_at) == today
            ).count()
            
            emails_month = Email.query.filter(
                Email.organization_id == org.id,
                Email.created_at >= month_start
            ).count()
        except:
            emails_today = 0
            emails_month = 0
        
        # Stats
        stats = {
            'total_domains': len(domains),
            'verified_domains': len(verified_domains),
            'emails_sent_today': emails_today,
            'emails_sent_month': emails_month
        }
        
        return render_template('dashboard/index.html', 
                             user=current_user,
                             org=org,
                             domains=domains,
                             stats=stats)
    except Exception as e:
        flash(f'Error loading dashboard: {e}', 'danger')
        return redirect(url_for('web.index'))

@dashboard_bp.route('/domains')
@login_required
def domains():
    """Domain management page"""
    org = current_user.organization
    
    if not org:
        flash('Organization not found.', 'danger')
        return redirect(url_for('dashboard.index'))
    
    domains = Domain.query.filter_by(
        organization_id=org.id
    ).order_by(Domain.created_at.desc()).all()
    
    return render_template('dashboard/domains.html', domains=domains, org=org, user=current_user)

@dashboard_bp.route('/settings')
@login_required
def settings():
    """Settings page"""
    org = current_user.organization
    
    if not org:
        flash('Organization not found.', 'danger')
        return redirect(url_for('dashboard.index'))
    
    return render_template('dashboard/settings.html', org=org, user=current_user)

@dashboard_bp.route('/api-keys/regenerate', methods=['POST'])
@login_required
def regenerate_api_keys():
    """Regenerate API keys"""
    try:
        org = current_user.organization
        
        if not org:
            return jsonify({'success': False, 'error': 'Organization not found'}), 404
        
        # Regenerate keys
        org.regenerate_api_key()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'api_key': org.api_key,
            'api_secret': org.api_secret,
            'message': 'API keys regenerated successfully'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@dashboard_bp.route('/send-email')
@login_required
def send_email():
    """Send email page"""
    org = current_user.organization
    
    if not org:
        flash('Organization not found.', 'danger')
        return redirect(url_for('dashboard.index'))
    
    # Get verified domains
    verified_domains = Domain.query.filter_by(
        organization_id=org.id,
        dns_verified=True,
        is_active=True
    ).all()
    
    return render_template('dashboard/send_email.html', 
                         org=org, 
                         user=current_user,
                         verified_domains=verified_domains)

@dashboard_bp.route('/bulk-send')
@login_required
def bulk_send():
    """Bulk email sending page"""
    org = current_user.organization
    
    if not org:
        flash('Organization not found.', 'danger')
        return redirect(url_for('dashboard.index'))
    
    # Get verified domains
    verified_domains = Domain.query.filter_by(
        organization_id=org.id,
        dns_verified=True,
        is_active=True
    ).all()
    
    return render_template('dashboard/bulk_send.html', 
                         org=org, 
                         user=current_user,
                         verified_domains=verified_domains)
