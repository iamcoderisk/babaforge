from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app import db
from app.models.user import User
from app.models.organization import Organization
from app.models.domain import Domain
from app.models.email import Email
from app.models.contact import Contact
from app.models.campaign import Campaign
from app.models.pricing import Subscription, PricingPlan
from sqlalchemy import func, text, and_, or_
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

admin_bp = Blueprint('admin', __name__, url_prefix='/hub')

def admin_required(f):
    """Decorator to require admin role"""
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Please log in to access the admin panel.', 'warning')
            return redirect(url_for('auth.login', next=request.url))
        
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
        # Date ranges
        today = datetime.utcnow().date()
        week_ago = datetime.utcnow() - timedelta(days=7)
        month_ago = datetime.utcnow() - timedelta(days=30)
        
        # User statistics
        total_users = User.query.count()
        active_users = User.query.filter_by(is_active=True).count()
        verified_users = User.query.filter_by(is_verified=True).count()
        new_users_today = User.query.filter(func.date(User.created_at) == today).count()
        new_users_week = User.query.filter(User.created_at >= week_ago).count()
        
        # Organization statistics
        total_orgs = Organization.query.count()
        active_orgs = Organization.query.filter_by(is_active=True).count()
        paying_orgs = Subscription.query.filter_by(status='active').count()
        
        # Domain statistics
        total_domains = Domain.query.count()
        verified_domains = Domain.query.filter_by(dns_verified=True).count()
        pending_domains = total_domains - verified_domains
        
        # Email statistics
        emails_today = Email.query.filter(func.date(Email.created_at) == today).count()
        emails_week = Email.query.filter(Email.created_at >= week_ago).count()
        emails_month = Email.query.filter(Email.created_at >= month_ago).count()
        
        emails_sent = Email.query.filter_by(status='sent').count()
        emails_failed = Email.query.filter_by(status='failed').count()
        emails_queued = Email.query.filter_by(status='queued').count()
        
        # Revenue statistics
        revenue_query = db.session.query(
            func.sum(PricingPlan.price).label('total')
        ).join(Subscription).filter(
            Subscription.status == 'active'
        ).first()
        
        monthly_revenue = float(revenue_query.total) if revenue_query.total else 0
        annual_revenue = monthly_revenue * 12
        
        # Recent activity
        recent_users = User.query.order_by(User.created_at.desc()).limit(10).all()
        recent_domains = Domain.query.order_by(Domain.created_at.desc()).limit(10).all()
        recent_emails = Email.query.order_by(Email.created_at.desc()).limit(20).all()
        
        # Top organizations by email volume
        top_orgs = db.session.query(
            Organization.id,
            Organization.name,
            Organization.is_active,
            func.count(Email.id).label('email_count')
        ).join(Email, Email.organization_id == Organization.id, isouter=True) \
         .group_by(Organization.id, Organization.name, Organization.is_active) \
         .order_by(func.count(Email.id).desc()) \
         .limit(10).all()
        
        # Delivery statistics
        delivery_rate = (emails_sent / (emails_sent + emails_failed) * 100) if (emails_sent + emails_failed) > 0 else 0
        
        stats = {
            'users': {
                'total': total_users,
                'active': active_users,
                'verified': verified_users,
                'new_today': new_users_today,
                'new_week': new_users_week
            },
            'organizations': {
                'total': total_orgs,
                'active': active_orgs,
                'paying': paying_orgs
            },
            'domains': {
                'total': total_domains,
                'verified': verified_domains,
                'pending': pending_domains
            },
            'emails': {
                'today': emails_today,
                'week': emails_week,
                'month': emails_month,
                'sent': emails_sent,
                'failed': emails_failed,
                'queued': emails_queued,
                'delivery_rate': round(delivery_rate, 2)
            },
            'revenue': {
                'monthly': monthly_revenue,
                'annual': annual_revenue,
                'arr': annual_revenue  # Annual Recurring Revenue
            }
        }
        
        return render_template('admin/hub_index.html',
                             stats=stats,
                             recent_users=recent_users,
                             recent_domains=recent_domains,
                             recent_emails=recent_emails,
                             top_orgs=top_orgs)
        
    except Exception as e:
        logger.error(f"Admin dashboard error: {e}")
        flash(f'Error loading dashboard: {e}', 'danger')
        return redirect(url_for('dashboard.index'))

@admin_bp.route('/users')
@login_required
@admin_required
def users():
    """User management page"""
    try:
        page = int(request.args.get('page', 1))
        per_page = 50
        search = request.args.get('search', '').strip()
        status = request.args.get('status', '')
        
        query = User.query
        
        if search:
            query = query.filter(
                or_(
                    User.email.ilike(f'%{search}%'),
                    User.first_name.ilike(f'%{search}%'),
                    User.last_name.ilike(f'%{search}%')
                )
            )
        
        if status == 'active':
            query = query.filter_by(is_active=True)
        elif status == 'inactive':
            query = query.filter_by(is_active=False)
        elif status == 'verified':
            query = query.filter_by(is_verified=True)
        elif status == 'unverified':
            query = query.filter_by(is_verified=False)
        
        pagination = query.order_by(User.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return render_template('admin/hub_users.html',
                             users=pagination.items,
                             pagination=pagination,
                             search=search,
                             status=status)
        
    except Exception as e:
        logger.error(f"List users error: {e}")
        flash(f'Error loading users: {e}', 'danger')
        return redirect(url_for('admin.index'))

@admin_bp.route('/user/<user_id>/block', methods=['POST'])
@login_required
@admin_required
def block_user(user_id):
    """Block a user"""
    try:
        user = User.query.get(user_id)
        if not user:
            return jsonify({'success': False, 'error': 'User not found'}), 404
        
        if user.role == 'admin':
            return jsonify({'success': False, 'error': 'Cannot block admin users'}), 403
        
        user.is_active = False
        
        # Also block their organization
        if user.organization:
            user.organization.is_active = False
        
        db.session.commit()
        
        logger.info(f"Admin {current_user.email} blocked user {user.email}")
        
        return jsonify({
            'success': True,
            'message': f'User {user.email} has been blocked'
        })
        
    except Exception as e:
        logger.error(f"Block user error: {e}")
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@admin_bp.route('/user/<user_id>/unblock', methods=['POST'])
@login_required
@admin_required
def unblock_user(user_id):
    """Unblock a user"""
    try:
        user = User.query.get(user_id)
        if not user:
            return jsonify({'success': False, 'error': 'User not found'}), 404
        
        user.is_active = True
        
        # Also unblock their organization
        if user.organization:
            user.organization.is_active = True
        
        db.session.commit()
        
        logger.info(f"Admin {current_user.email} unblocked user {user.email}")
        
        return jsonify({
            'success': True,
            'message': f'User {user.email} has been unblocked'
        })
        
    except Exception as e:
        logger.error(f"Unblock user error: {e}")
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@admin_bp.route('/user/<user_id>/details')
@login_required
@admin_required
def user_details(user_id):
    """View detailed user information"""
    try:
        user = User.query.get(user_id)
        if not user:
            flash('User not found', 'danger')
            return redirect(url_for('admin.users'))
        
        org = user.organization
        
        # Get user's email statistics
        email_stats = db.session.query(
            func.count(Email.id).label('total'),
            func.sum(func.case((Email.status == 'sent', 1), else_=0)).label('sent'),
            func.sum(func.case((Email.status == 'failed', 1), else_=0)).label('failed')
        ).filter(Email.organization_id == org.id).first() if org else None
        
        # Get domains
        domains = Domain.query.filter_by(organization_id=org.id).all() if org else []
        
        # Get recent emails
        recent_emails = Email.query.filter_by(
            organization_id=org.id
        ).order_by(Email.created_at.desc()).limit(20).all() if org else []
        
        return render_template('admin/hub_user_details.html',
                             user=user,
                             org=org,
                             email_stats=email_stats,
                             domains=domains,
                             recent_emails=recent_emails)
        
    except Exception as e:
        logger.error(f"User details error: {e}")
        flash(f'Error loading user details: {e}', 'danger')
        return redirect(url_for('admin.users'))

@admin_bp.route('/sales')
@login_required
@admin_required
def sales():
    """Sales and revenue dashboard"""
    try:
        # Get all active subscriptions
        subscriptions = db.session.query(
            Subscription,
            PricingPlan,
            Organization,
            User
        ).join(PricingPlan, Subscription.plan_id == PricingPlan.id) \
         .join(Organization, Subscription.organization_id == Organization.id) \
         .join(User, and_(User.organization_id == Organization.id, User.role == 'owner'), isouter=True) \
         .filter(Subscription.status == 'active') \
         .order_by(Subscription.created_at.desc()).all()
        
        # Calculate revenue
        total_mrr = sum(float(sub.PricingPlan.price) for sub in subscriptions)
        total_arr = total_mrr * 12
        
        # Revenue by plan
        revenue_by_plan = db.session.query(
            PricingPlan.name,
            PricingPlan.price,
            func.count(Subscription.id).label('subscribers'),
            (PricingPlan.price * func.count(Subscription.id)).label('revenue')
        ).join(Subscription).filter(Subscription.status == 'active') \
         .group_by(PricingPlan.name, PricingPlan.price).all()
        
        return render_template('admin/hub_sales.html',
                             subscriptions=subscriptions,
                             total_mrr=total_mrr,
                             total_arr=total_arr,
                             revenue_by_plan=revenue_by_plan)
        
    except Exception as e:
        logger.error(f"Sales dashboard error: {e}")
        flash(f'Error loading sales data: {e}', 'danger')
        return redirect(url_for('admin.index'))

@admin_bp.route('/delivery')
@login_required
@admin_required
def delivery():
    """Email delivery monitoring"""
    try:
        page = int(request.args.get('page', 1))
        per_page = 100
        status = request.args.get('status', '')
        org_id = request.args.get('org_id', '')
        
        query = Email.query
        
        if status:
            query = query.filter_by(status=status)
        
        if org_id:
            query = query.filter_by(organization_id=org_id)
        
        pagination = query.order_by(Email.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        # Delivery statistics
        total_emails = Email.query.count()
        sent_emails = Email.query.filter_by(status='sent').count()
        failed_emails = Email.query.filter_by(status='failed').count()
        queued_emails = Email.query.filter_by(status='queued').count()
        
        delivery_rate = (sent_emails / total_emails * 100) if total_emails > 0 else 0
        
        # Get organizations for filter
        organizations = Organization.query.order_by(Organization.name).all()
        
        return render_template('admin/hub_delivery.html',
                             emails=pagination.items,
                             pagination=pagination,
                             total_emails=total_emails,
                             sent_emails=sent_emails,
                             failed_emails=failed_emails,
                             queued_emails=queued_emails,
                             delivery_rate=round(delivery_rate, 2),
                             organizations=organizations,
                             current_status=status,
                             current_org=org_id)
        
    except Exception as e:
        logger.error(f"Delivery monitoring error: {e}")
        flash(f'Error loading delivery data: {e}', 'danger')
        return redirect(url_for('admin.index'))

@admin_bp.route('/analytics')
@login_required
@admin_required
def analytics():
    """Advanced analytics dashboard"""
    try:
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
        
        # Daily user signups
        user_signups = db.session.query(
            func.date(User.created_at).label('date'),
            func.count(User.id).label('signups')
        ).filter(
            User.created_at >= start_date
        ).group_by(func.date(User.created_at)).order_by('date').all()
        
        # Format for charts
        chart_data = {
            'dates': [str(stat.date) for stat in daily_stats],
            'emails_total': [stat.total for stat in daily_stats],
            'emails_sent': [stat.sent for stat in daily_stats],
            'emails_failed': [stat.failed for stat in daily_stats],
            'signups': dict((str(s.date), s.signups) for s in user_signups)
        }
        
        return render_template('admin/hub_analytics.html',
                             chart_data=chart_data,
                             days=days)
        
    except Exception as e:
        logger.error(f"Analytics error: {e}")
        flash(f'Error loading analytics: {e}', 'danger')
        return redirect(url_for('admin.index'))

@admin_bp.route('/api/stats/realtime')
@login_required
@admin_required
def realtime_stats():
    """Real-time statistics API"""
    try:
        stats = {
            'emails_queued': Email.query.filter_by(status='queued').count(),
            'emails_sending': Email.query.filter_by(status='sending').count(),
            'campaigns_active': Campaign.query.filter_by(status='sending').count(),
            'active_users_online': User.query.filter(
                User.last_seen > datetime.utcnow() - timedelta(minutes=5)
            ).count() if hasattr(User, 'last_seen') else 0,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        return jsonify({'success': True, 'stats': stats})
        
    except Exception as e:
        logger.error(f"Realtime stats error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500
