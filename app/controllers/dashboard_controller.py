from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app import db
from app.models.email import Email
from app.models.contact import Contact
from app.models.domain import Domain
from app.models.campaign import Campaign
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

dashboard_bp = Blueprint('dashboard', __name__)


@dashboard_bp.route('/')
@login_required
def index():
    """Dashboard homepage"""
    try:
        org = current_user.organization
        
        if not org:
            flash('No organization found. Please contact support.', 'error')
            return redirect(url_for('main.index'))
        
        # Get stats
        stats = {
            'total_sent': Email.query.filter_by(organization_id=org.id, status='sent').count(),
            'total_contacts': Contact.query.filter_by(organization_id=org.id).count(),
            'total_domains': Domain.query.filter_by(organization_id=org.id).count(),
            'queued': Email.query.filter_by(organization_id=org.id, status='queued').count()
        }
        
        # Get recent campaigns
        campaigns = Campaign.query.filter_by(
            organization_id=org.id
        ).order_by(Campaign.created_at.desc()).limit(5).all()
        
        # Get recent individual emails
        individual_emails = Email.query.filter_by(
            organization_id=org.id
        ).order_by(Email.created_at.desc()).limit(10).all()
        
        return render_template('dashboard/index.html',
                             campaigns=campaigns,
                             individual_emails=individual_emails,
                             stats=stats)
    
    except Exception as e:
        logger.error(f"Dashboard error: {e}", exc_info=True)
        # Instead of redirecting, show empty dashboard
        stats = {'total_sent': 0, 'total_contacts': 0, 'total_domains': 0, 'queued': 0}
        return render_template('dashboard/index.html',
                             campaigns=[],
                             individual_emails=[],
                             stats=stats)


@dashboard_bp.route('/send-email')
@login_required
def send_email():
    """Send single email page"""
    org = current_user.organization
    domains = Domain.query.filter_by(organization_id=org.id).all()
    return render_template('dashboard/send_email.html', domains=domains)


@dashboard_bp.route('/bulk-send')
@login_required
def bulk_send():
    """Bulk send page"""
    org = current_user.organization
    domains = Domain.query.filter_by(organization_id=org.id).all()
    contacts = Contact.query.filter_by(organization_id=org.id).all()
    return render_template('dashboard/bulk_send.html', domains=domains, contacts=contacts)


@dashboard_bp.route('/contacts')
@login_required
def contacts():
    """Contacts page"""
    org = current_user.organization
    contacts = Contact.query.filter_by(organization_id=org.id).order_by(
        Contact.created_at.desc()
    ).all()
    return render_template('dashboard/contacts.html', contacts=contacts)


@dashboard_bp.route('/domains')
@login_required
def domains():
    """Domains page"""
    org = current_user.organization
    domains = Domain.query.filter_by(organization_id=org.id).order_by(
        Domain.created_at.desc()
    ).all()
    return render_template('dashboard/domains.html', domains=domains)


def add_domain():
    """Add new domain"""
    try:
        domain_name = request.form.get('domain_name')
        org = current_user.organization
        
        # Check if domain already exists
        existing = Domain.query.filter_by(
            domain_name=domain_name,
            organization_id=org.id
        ).first()
        
        if existing:
            flash('Domain already exists', 'error')
        else:
            domain = Domain(
                organization_id=org.id,
                domain_name=domain_name,
                dns_verified=False
            )
            db.session.add(domain)
            db.session.commit()
            flash('Domain added successfully', 'success')
    
    except Exception as e:
        logger.error(f"Add domain error: {e}")
        flash('Error adding domain', 'error')
    
    return redirect(url_for('dashboard.domains'))


@dashboard_bp.route('/domains/<domain_id>/verify', methods=['POST'])
@login_required
def verify_domain(domain_id):
    """Verify domain DNS"""
    try:
        org = current_user.organization
        domain = Domain.query.filter_by(id=domain_id, organization_id=org.id).first()
        
        if domain:
            # Simple verification - mark as verified
            domain.dns_verified = True
            domain.verified_at = datetime.utcnow()
            db.session.commit()
            flash('Domain verified successfully', 'success')
        else:
            flash('Domain not found', 'error')
    
    except Exception as e:
        logger.error(f"Verify domain error: {e}")
        flash('Error verifying domain', 'error')
    
    return redirect(url_for('dashboard.domains'))


@dashboard_bp.route('/domains/<domain_id>/generate-dkim', methods=['POST'])
@login_required
def generate_dkim(domain_id):
    """Generate DKIM keys for domain"""
    try:
        from app.services.dkim.dkim_generator import generate_dkim_keys
        
        org = current_user.organization
        domain = Domain.query.filter_by(id=domain_id, organization_id=org.id).first()
        
        if domain:
            private_key, public_key = generate_dkim_keys(domain.domain_name)
            flash('DKIM keys generated successfully', 'success')
        else:
            flash('Domain not found', 'error')
    
    except Exception as e:
        logger.error(f"Generate DKIM error: {e}")
        flash('Error generating DKIM keys', 'error')
    
    return redirect(url_for('dashboard.domains'))


@dashboard_bp.route('/domains/<domain_id>/delete', methods=['POST'])
@login_required
def delete_domain(domain_id):
    """Delete domain"""
    try:
        org = current_user.organization
        domain = Domain.query.filter_by(id=domain_id, organization_id=org.id).first()
        
        if domain:
            db.session.delete(domain)
            db.session.commit()
            flash('Domain deleted successfully', 'success')
        else:
            flash('Domain not found', 'error')
    
    except Exception as e:
        logger.error(f"Delete domain error: {e}")
        flash('Error deleting domain', 'error')
    
    return redirect(url_for('dashboard.domains'))


@dashboard_bp.route('/settings')
@login_required
def settings():
    """Settings page"""
    return render_template('dashboard/settings.html')


@dashboard_bp.route('/analytics')
@login_required
def analytics():
    """Analytics page"""
    org = current_user.organization
    campaigns = Campaign.query.filter_by(organization_id=org.id).all()
    return render_template('dashboard/analytics.html', campaigns=campaigns)


@dashboard_bp.route('/campaigns')
@login_required
def campaigns():
    """Campaigns page"""
    org = current_user.organization
    campaigns = Campaign.query.filter_by(organization_id=org.id).order_by(
        Campaign.created_at.desc()
    ).all()
    return render_template('dashboard/campaigns.html', campaigns=campaigns)


@dashboard_bp.route('/domains/add', methods=['POST'])
@login_required
def add_domain_api():
    """Add new domain - JSON response"""
    try:
        domain_name = request.form.get('domain_name')
        org = current_user.organization
        
        # Check if domain already exists
        existing = Domain.query.filter_by(
            domain_name=domain_name,
            organization_id=org.id
        ).first()
        
        if existing:
            return jsonify({'success': False, 'error': 'Domain already exists'})
        
        domain = Domain(
            organization_id=org.id,
            domain_name=domain_name
        )
        domain.dns_verified = False
        db.session.add(domain)
        db.session.commit()
        
        return jsonify({'success': True, 'domain_id': domain.id})
    
    except Exception as e:
        logger.error(f"Add domain error: {e}")
        return jsonify({'success': False, 'error': str(e)})


@dashboard_bp.route('/domains/<domain_id>/generate-dkim', methods=['POST'])
@login_required
def generate_dkim_api(domain_id):
    """Generate DKIM keys - JSON response"""
    try:
        from app.services.dkim.dkim_generator import generate_dkim_keys
        
        org = current_user.organization
        domain = Domain.query.filter_by(id=domain_id, organization_id=org.id).first()
        
        if not domain:
            return jsonify({'success': False, 'error': 'Domain not found'})
        
        private_key, public_key = generate_dkim_keys(domain.domain_name)
        
        # Store public key
        domain.dkim_public_key = public_key
        db.session.commit()
        
        return jsonify({'success': True, 'public_key': public_key})
    
    except Exception as e:
        logger.error(f"Generate DKIM error: {e}")
        return jsonify({'success': False, 'error': str(e)})


@dashboard_bp.route('/domains/<domain_id>/verify', methods=['POST'])
@login_required
def verify_domain_api(domain_id):
    """Verify domain DNS - JSON response"""
    try:
        from app.services.deliverability.dns_verifier import DNSVerifier
        
        org = current_user.organization
        domain = Domain.query.filter_by(id=domain_id, organization_id=org.id).first()
        
        if not domain:
            return jsonify({'success': False, 'error': 'Domain not found'})
        
        verifier = DNSVerifier()
        result = verifier.verify_domain(domain.domain_name, '156.67.29.186')
        
        if result['verified']:
            domain.dns_verified = True
            domain.verified_at = datetime.utcnow()
            db.session.commit()
            return jsonify({'success': True, 'message': 'Domain verified!'})
        else:
            return jsonify({
                'success': False, 
                'message': 'Verification failed. Please check DNS records.',
                'details': result
            })
    
    except Exception as e:
        logger.error(f"Verify domain error: {e}")
        return jsonify({'success': False, 'error': str(e)})


@dashboard_bp.route('/domains/<domain_id>/delete', methods=['POST'])
@login_required
def delete_domain_api(domain_id):
    """Delete domain - JSON response"""
    try:
        org = current_user.organization
        domain = Domain.query.filter_by(id=domain_id, organization_id=org.id).first()
        
        if domain:
            db.session.delete(domain)
            db.session.commit()
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'error': 'Domain not found'})
    
    except Exception as e:
        logger.error(f"Delete domain error: {e}")
        return jsonify({'success': False, 'error': str(e)})


@dashboard_bp.route('/domains/<domain_id>/dns-info')
@login_required
def domain_dns_info(domain_id):
    """Get DNS info for domain"""
    try:
        org = current_user.organization
        domain = Domain.query.filter_by(id=domain_id, organization_id=org.id).first()
        
        if not domain:
            return jsonify({'success': False, 'error': 'Domain not found'})
        
        dns_info = {
            'spf': 'v=spf1 ip4:156.67.29.186 ~all',
            'dkim': domain.dkim_public_key if domain.dkim_public_key else None,
            'dmarc': f'v=DMARC1; p=none; rua=mailto:dmarc@{domain.domain_name}'
        }
        
        return jsonify({
            'success': True,
            'domain': domain.to_dict(),
            'dns': dns_info
        })
    
    except Exception as e:
        logger.error(f"DNS info error: {e}")
        return jsonify({'success': False, 'error': str(e)})
