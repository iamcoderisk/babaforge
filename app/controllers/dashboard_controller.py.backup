from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app import db
from app.models.email import Email
from app.models.campaign import Campaign
from app.models.contact import Contact
from app.models.domain import Domain
from sqlalchemy import func, or_
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/dashboard')

@dashboard_bp.route('/')
@login_required
def index():
    """Main dashboard"""
    try:
        org = current_user.organization
        
        if not org:
            flash('Organization not found. Please contact support.', 'danger')
            return redirect(url_for('web.index'))
        
        # Date ranges
        today = datetime.utcnow().date()
        month_start = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        # Email statistics - TODAY
        try:
            emails_today = Email.query.filter(
                Email.organization_id == org.id,
                func.date(Email.created_at) == today
            ).count()
        except Exception as e:
            logger.error(f"Error counting emails today: {e}")
            emails_today = 0
        
        try:
            emails_sent_today = Email.query.filter(
                Email.organization_id == org.id,
                func.date(Email.created_at) == today,
                Email.status == 'sent'
            ).count()
        except Exception as e:
            logger.error(f"Error counting sent emails today: {e}")
            emails_sent_today = 0
        
        # Email statistics - THIS MONTH
        try:
            emails_this_month = Email.query.filter(
                Email.organization_id == org.id,
                Email.created_at >= month_start
            ).count()
        except Exception as e:
            logger.error(f"Error counting emails this month: {e}")
            emails_this_month = 0
        
        try:
            emails_sent_this_month = Email.query.filter(
                Email.organization_id == org.id,
                Email.created_at >= month_start,
                Email.status == 'sent'
            ).count()
        except Exception as e:
            logger.error(f"Error counting sent emails this month: {e}")
            emails_sent_this_month = 0
        
        # Open rate
        try:
            emails_opened = Email.query.filter(
                Email.organization_id == org.id,
                Email.opened == True
            ).count() if hasattr(Email, 'opened') else 0
        except Exception as e:
            logger.error(f"Error counting opened emails: {e}")
            emails_opened = 0
        
        try:
            total_delivered = Email.query.filter(
                Email.organization_id == org.id,
                Email.status == 'sent'
            ).count()
        except Exception as e:
            logger.error(f"Error counting delivered emails: {e}")
            total_delivered = 0
        
        open_rate = (emails_opened / total_delivered * 100) if total_delivered > 0 else 0
        
        # Click rate
        try:
            from app.models.email_tracking import EmailClick
            
            emails_clicked = db.session.query(Email.id).join(
                EmailClick, Email.id == EmailClick.email_id
            ).filter(
                Email.organization_id == org.id
            ).distinct().count()
        except Exception as e:
            logger.error(f"Error counting clicked emails: {e}")
            emails_clicked = 0
        
        click_rate = (emails_clicked / total_delivered * 100) if total_delivered > 0 else 0
        
        # Delivery rate
        delivery_rate = (emails_sent_this_month / emails_this_month * 100) if emails_this_month > 0 else 0
        
        # Contact count
        try:
            contacts_count = Contact.query.filter_by(organization_id=org.id).count()
        except Exception as e:
            logger.error(f"Error counting contacts: {e}")
            contacts_count = 0
        
        # Campaign count
        try:
            campaigns_count = Campaign.query.filter_by(organization_id=org.id).count()
            active_campaigns = Campaign.query.filter_by(
                organization_id=org.id,
                status='sending'
            ).count()
        except Exception as e:
            logger.error(f"Error counting campaigns: {e}")
            campaigns_count = 0
            active_campaigns = 0
        
        # Recent activity
        try:
            recent_emails = Email.query.filter_by(
                organization_id=org.id
            ).order_by(Email.created_at.desc()).limit(10).all()
            
            # Get tracking data if available
            if hasattr(Email, 'opened'):
                try:
                    from app.models.email_tracking import EmailOpen, EmailClick
                    
                    for email in recent_emails:
                        email.opens = EmailOpen.query.filter_by(email_id=email.id).count()
                        email.clicks = EmailClick.query.filter_by(email_id=email.id).count()
                except Exception as e:
                    logger.error(f"Error getting tracking data: {e}")
                    for email in recent_emails:
                        email.opens = 0
                        email.clicks = 0
            else:
                for email in recent_emails:
                    email.opens = 0
                    email.clicks = 0
                    
        except Exception as e:
            logger.error(f"Error getting recent emails: {e}")
            recent_emails = []
        
        # Unsubscribe count
        try:
            from app.models.email_tracking import EmailUnsubscribe
            unsubscribe_count = EmailUnsubscribe.query.filter_by(
                organization_id=org.id
            ).count()
        except Exception as e:
            logger.error(f"Error counting unsubscribes: {e}")
            unsubscribe_count = 0
        
        stats = {
            'emails_today': emails_today,
            'emails_sent_today': emails_sent_today,
            'emails_this_month': emails_this_month,
            'emails_sent_this_month': emails_sent_this_month,
            'open_rate': round(open_rate, 1),
            'click_rate': round(click_rate, 1),
            'delivery_rate': round(delivery_rate, 1),
            'contacts': contacts_count,
            'campaigns': campaigns_count,
            'active_campaigns': active_campaigns,
            'unsubscribes': unsubscribe_count
        }
        
        return render_template('dashboard/index.html',
                             org=org,
                             stats=stats,
                             recent_emails=recent_emails)
    
    except Exception as e:
        logger.error(f"Dashboard error: {e}", exc_info=True)
        flash(f'Error loading dashboard: {str(e)}', 'danger')
        return redirect(url_for('web.index'))

@dashboard_bp.route('/send-email')
@login_required
def send_email():
    """Send email page"""
    org = current_user.organization
    domains = Domain.query.filter_by(organization_id=org.id).all() if org else []
    return render_template('dashboard/send_email.html', org=org, domains=domains)

@dashboard_bp.route('/bulk-send')
@login_required
def bulk_send():
    """Bulk send page"""
    try:
        org = current_user.organization
        
        if not org:
            flash('Organization not found.', 'danger')
            return redirect(url_for('dashboard.index'))
        
        # Get verified domains only
        domains = Domain.query.filter_by(
            organization_id=org.id,
            dns_verified=True
        ).all()
        
        return render_template('dashboard/bulk_send.html', org=org, domains=domains)
    
    except Exception as e:
        logger.error(f"Bulk send page error: {e}", exc_info=True)
        flash(f'Error loading bulk send page: {str(e)}', 'danger')
        return redirect(url_for('dashboard.index'))

@dashboard_bp.route('/contacts')
@login_required
def contacts():
    """Contacts page"""
    try:
        org = current_user.organization
        
        if not org:
            flash('Organization not found.', 'danger')
            return redirect(url_for('dashboard.index'))
        
        page = request.args.get('page', 1, type=int)
        search = request.args.get('search', '').strip()
        
        query = Contact.query.filter_by(organization_id=org.id)
        
        if search:
            query = query.filter(
                or_(
                    Contact.email.ilike(f'%{search}%'),
                    Contact.first_name.ilike(f'%{search}%'),
                    Contact.last_name.ilike(f'%{search}%'),
                    Contact.company.ilike(f'%{search}%')
                )
            )
        
        contacts_pagination = query.order_by(Contact.created_at.desc()).paginate(
            page=page, per_page=50, error_out=False
        )
        
        return render_template('dashboard/contacts.html', 
                             org=org, 
                             contacts=contacts_pagination)
    
    except Exception as e:
        logger.error(f"Contacts page error: {e}", exc_info=True)
        flash(f'Error loading contacts: {str(e)}', 'danger')
        return redirect(url_for('dashboard.index'))

@dashboard_bp.route('/domains')
@login_required
def domains():
    """Domains page"""
    org = current_user.organization
    domains = Domain.query.filter_by(organization_id=org.id).all() if org else []
    return render_template('dashboard/domains.html', org=org, domains=domains)

@dashboard_bp.route('/settings')
@login_required
def settings():
    """Settings page"""
    org = current_user.organization
    return render_template('dashboard/settings.html', org=org)

@dashboard_bp.route('/analytics')
@login_required
def analytics():
    """Detailed analytics page"""
    try:
        org = current_user.organization
        
        # Check if tracking tables exist
        try:
            from app.models.email_tracking import EmailOpen, EmailClick, EmailUnsubscribe
            
            # Get emails with tracking data
            emails = db.session.query(
                Email,
                func.count(EmailOpen.id).label('opens'),
                func.count(EmailClick.id).label('clicks')
            ).outerjoin(EmailOpen, Email.id == EmailOpen.email_id) \
             .outerjoin(EmailClick, Email.id == EmailClick.email_id) \
             .filter(Email.organization_id == org.id) \
             .group_by(Email.id) \
             .order_by(Email.created_at.desc()) \
             .limit(100).all()
            
            # Get click details
            recent_clicks = db.session.query(
                EmailClick,
                Email
            ).join(Email, EmailClick.email_id == Email.id) \
             .filter(Email.organization_id == org.id) \
             .order_by(EmailClick.clicked_at.desc()) \
             .limit(50).all()
            
            # Get unsubscribes
            unsubscribes = EmailUnsubscribe.query.filter_by(
                organization_id=org.id
            ).order_by(EmailUnsubscribe.unsubscribed_at.desc()).all()
            
        except Exception as e:
            logger.error(f"Error loading tracking data: {e}")
            
            # Fallback to basic email list
            emails = [(email, 0, 0) for email in Email.query.filter_by(
                organization_id=org.id
            ).order_by(Email.created_at.desc()).limit(100).all()]
            
            recent_clicks = []
            unsubscribes = []
        
        return render_template('dashboard/analytics.html',
                             org=org,
                             emails=emails,
                             recent_clicks=recent_clicks,
                             unsubscribes=unsubscribes)
    
    except Exception as e:
        logger.error(f"Analytics error: {e}", exc_info=True)
        flash(f'Error loading analytics: {str(e)}', 'danger')
        return redirect(url_for('dashboard.index'))
