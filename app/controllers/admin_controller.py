from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app import db
from app.models.user import User
from app.models.organization import Organization
from app.models.domain import Domain
from app.models.email import Email
from app.models.contact import Contact, BulkImport
from app.models.campaign import Campaign, EmailTemplate
from sqlalchemy import func, text
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

def admin_required(f):
    """Decorator to require admin role"""
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('auth.login'))
        
        if current_user.role != 'admin':
            flash('Access denied. Admin privileges required.', 'danger')
            return redirect(url_for('dashboard.index'))
        
        return f(*args, **kwargs)
    return decorated_function

@admin_bp.route('/')
@login_required
@admin_required
def index():
    """Admin dashboard overview"""
    try:
        # System-wide statistics
        total_users = User.query.count()
        total_organizations = Organization.query.count()
        total_domains = Domain.query.count()
        verified_domains = Domain.query.filter_by(dns_verified=True).count()
        total_contacts = Contact.query.count()
        total_campaigns = Campaign.query.count()
        
        # Email statistics
        today = datetime.utcnow().date()
        week_ago = datetime.utcnow() - timedelta(days=7)
        month_ago = datetime.utcnow() - timedelta(days=30)
        
        emails_today = Email.query.filter(
            func.date(Email.created_at) == today
        ).count()
        
        emails_week = Email.query.filter(
            Email.created_at >= week_ago
        ).count()
        
        emails_month = Email.query.filter(
            Email.created_at >= month_ago
        ).count()
        
        # Status breakdown
        emails_sent = Email.query.filter_by(status='sent').count()
        emails_failed = Email.query.filter_by(status='failed').count()
        emails_queued = Email.query.filter_by(status='queued').count()
        
        # Recent activity
        recent_users = User.query.order_by(User.created_at.desc()).limit(5).all()
        recent_domains = Domain.query.order_by(Domain.created_at.desc()).limit(5).all()
        recent_campaigns = Campaign.query.order_by(Campaign.created_at.desc()).limit(5).all()
        
        # Top organizations by email volume
        top_orgs = db.session.query(
            Organization.id,
            Organization.name,
            func.count(Email.id).label('email_count')
        ).join(Email, Email.organization_id == Organization.id) \
         .group_by(Organization.id, Organization.name) \
         .order_by(func.count(Email.id).desc()) \
         .limit(10).all()
        
        stats = {
            'users': {
                'total': total_users,
                'active': User.query.filter_by(is_active=True).count(),
                'verified': User.query.filter_by(is_verified=True).count()
            },
            'organizations': {
                'total': total_organizations,
                'active': Organization.query.filter_by(is_active=True).count()
            },
            'domains': {
                'total': total_domains,
                'verified': verified_domains,
                'pending': total_domains - verified_domains
            },
            'emails': {
                'today': emails_today,
                'week': emails_week,
                'month': emails_month,
                'sent': emails_sent,
                'failed': emails_failed,
                'queued': emails_queued
            },
            'contacts': {
                'total': total_contacts,
                'active': Contact.query.filter_by(status='active').count(),
                'unsubscribed': Contact.query.filter_by(status='unsubscribed').count()
            },
            'campaigns': {
                'total': total_campaigns,
                'draft': Campaign.query.filter_by(status='draft').count(),
                'sent': Campaign.query.filter_by(status='sent').count(),
                'scheduled': Campaign.query.filter_by(status='scheduled').count()
            }
        }
        
        return render_template('admin/index.html',
                             stats=stats,
                             recent_users=recent_users,
                             recent_domains=recent_domains,
                             recent_campaigns=recent_campaigns,
                             top_orgs=top_orgs)
        
    except Exception as e:
        logger.error(f"Admin dashboard error: {e}")
        flash(f'Error loading dashboard: {e}', 'danger')
        return redirect(url_for('dashboard.index'))

@admin_bp.route('/users')
@login_required
@admin_required
def users():
    """List all users"""
    try:
        page = int(request.args.get('page', 1))
        per_page = 50
        
        search = request.args.get('search', '').strip()
        
        query = User.query
        
        if search:
            query = query.filter(
                db.or_(
                    User.email.ilike(f'%{search}%'),
                    User.first_name.ilike(f'%{search}%'),
                    User.last_name.ilike(f'%{search}%')
                )
            )
        
        pagination = query.order_by(User.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return render_template('admin/users.html',
                             users=pagination.items,
                             pagination=pagination)
        
    except Exception as e:
        logger.error(f"List users error: {e}")
        flash(f'Error loading users: {e}', 'danger')
        return redirect(url_for('admin.index'))

@admin_bp.route('/organizations')
@login_required
@admin_required
def organizations():
    """List all organizations"""
    try:
        page = int(request.args.get('page', 1))
        per_page = 50
        
        pagination = Organization.query.order_by(
            Organization.created_at.desc()
        ).paginate(page=page, per_page=per_page, error_out=False)
        
        # Get email counts for each org
        org_stats = {}
        for org in pagination.items:
            email_count = Email.query.filter_by(organization_id=org.id).count()
            domain_count = Domain.query.filter_by(organization_id=org.id).count()
            user_count = User.query.filter_by(organization_id=org.id).count()
            
            org_stats[org.id] = {
                'emails': email_count,
                'domains': domain_count,
                'users': user_count
            }
        
        return render_template('admin/organizations.html',
                             organizations=pagination.items,
                             pagination=pagination,
                             org_stats=org_stats)
        
    except Exception as e:
        logger.error(f"List organizations error: {e}")
        flash(f'Error loading organizations: {e}', 'danger')
        return redirect(url_for('admin.index'))

@admin_bp.route('/emails')
@login_required
@admin_required
def emails():
    """List all emails"""
    try:
        page = int(request.args.get('page', 1))
        per_page = 100
        status = request.args.get('status')
        
        query = Email.query
        
        if status:
            query = query.filter_by(status=status)
        
        pagination = query.order_by(Email.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return render_template('admin/emails.html',
                             emails=pagination.items,
                             pagination=pagination,
                             current_status=status)
        
    except Exception as e:
        logger.error(f"List emails error: {e}")
        flash(f'Error loading emails: {e}', 'danger')
        return redirect(url_for('admin.index'))

@admin_bp.route('/domains')
@login_required
@admin_required
def domains():
    """List all domains"""
    try:
        page = int(request.args.get('page', 1))
        per_page = 50
        
        verified_filter = request.args.get('verified')
        
        query = Domain.query
        
        if verified_filter == 'true':
            query = query.filter_by(dns_verified=True)
        elif verified_filter == 'false':
            query = query.filter_by(dns_verified=False)
        
        pagination = query.order_by(Domain.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return render_template('admin/domains.html',
                             domains=pagination.items,
                             pagination=pagination)
        
    except Exception as e:
        logger.error(f"List domains error: {e}")
        flash(f'Error loading domains: {e}', 'danger')
        return redirect(url_for('admin.index'))

@admin_bp.route('/campaigns')
@login_required
@admin_required
def campaigns():
    """List all campaigns"""
    try:
        page = int(request.args.get('page', 1))
        per_page = 50
        
        pagination = Campaign.query.order_by(Campaign.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return render_template('admin/campaigns.html',
                             campaigns=pagination.items,
                             pagination=pagination)
        
    except Exception as e:
        logger.error(f"List campaigns error: {e}")
        flash(f'Error loading campaigns: {e}', 'danger')
        return redirect(url_for('admin.index'))

@admin_bp.route('/analytics')
@login_required
@admin_required
def analytics():
    """Analytics dashboard"""
    try:
        # Get date range from query params
        days = int(request.args.get('days', 30))
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Daily email stats
        daily_stats = db.session.query(
            func.date(Email.created_at).label('date'),
            func.count(Email.id).label('total'),
            func.sum(func.case((Email.status == 'sent', 1), else_=0)).label('sent'),
            func.sum(func.case((Email.status == 'failed', 1), else_=0)).label('failed')
        ).filter(
            Email.created_at >= start_date
        ).group_by(func.date(Email.created_at)).order_by('date').all()
        
        # Format for charts
        chart_data = {
            'dates': [str(stat.date) for stat in daily_stats],
            'total': [stat.total for stat in daily_stats],
            'sent': [stat.sent for stat in daily_stats],
            'failed': [stat.failed for stat in daily_stats]
        }
        
        return render_template('admin/analytics.html',
                             chart_data=chart_data,
                             days=days)
        
    except Exception as e:
        logger.error(f"Analytics error: {e}")
        flash(f'Error loading analytics: {e}', 'danger')
        return redirect(url_for('admin.index'))

# API endpoints for admin actions

@admin_bp.route('/user/<user_id>/toggle-active', methods=['POST'])
@login_required
@admin_required
def toggle_user_active(user_id):
    """Toggle user active status"""
    try:
        user = User.query.get(user_id)
        if not user:
            return jsonify({'success': False, 'error': 'User not found'}), 404
        
        user.is_active = not user.is_active
        db.session.commit()
        
        return jsonify({
            'success': True,
            'is_active': user.is_active,
            'message': f"User {'activated' if user.is_active else 'deactivated'}"
        })
        
    except Exception as e:
        logger.error(f"Toggle user error: {e}")
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@admin_bp.route('/organization/<org_id>/toggle-active', methods=['POST'])
@login_required
@admin_required
def toggle_org_active(org_id):
    """Toggle organization active status"""
    try:
        org = Organization.query.get(org_id)
        if not org:
            return jsonify({'success': False, 'error': 'Organization not found'}), 404
        
        org.is_active = not org.is_active
        db.session.commit()
        
        return jsonify({
            'success': True,
            'is_active': org.is_active,
            'message': f"Organization {'activated' if org.is_active else 'deactivated'}"
        })
        
    except Exception as e:
        logger.error(f"Toggle org error: {e}")
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@admin_bp.route('/stats/api')
@login_required
@admin_required
def stats_api():
    """Real-time stats API for dashboard"""
    try:
        # Get real-time counts
        stats = {
            'emails_queued': Email.query.filter_by(status='queued').count(),
            'emails_sending': Email.query.filter_by(status='sending').count(),
            'campaigns_sending': Campaign.query.filter_by(status='sending').count(),
            'active_users': User.query.filter_by(is_active=True).count(),
            'timestamp': datetime.utcnow().isoformat()
        }
        
        return jsonify({'success': True, 'stats': stats})
        
    except Exception as e:
        logger.error(f"Stats API error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500
