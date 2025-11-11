from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from app import db
from sqlalchemy import text
import logging

logger = logging.getLogger(__name__)

dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/dashboard')

@dashboard_bp.route('/')
@login_required
def index():
    """Dashboard with real stats"""
    try:
        # Get real stats
        stats_result = db.session.execute(
            text("""
                SELECT 
                    COALESCE(SUM(emails_sent), 0) as emails_this_month,
                    (SELECT COUNT(*) FROM contacts WHERE organization_id = :org_id) as total_contacts,
                    (SELECT COUNT(*) FROM domains WHERE organization_id = :org_id) as domains_count,
                    0 as queued
                FROM campaigns 
                WHERE organization_id = :org_id
                AND created_at >= date_trunc('month', CURRENT_DATE)
            """),
            {'org_id': current_user.organization_id}
        )
        
        row = stats_result.fetchone()
        stats = {
            'emails_sent': int(row[0]) if row and row[0] else 0,
            'total_contacts': int(row[1]) if row and row[1] else 0,
            'domains': int(row[2]) if row and row[2] else 0,
            'queued': 0
        }
        
        # Get recent campaigns
        campaigns_result = db.session.execute(
            text("""
                SELECT 
                    id,
                    name,
                    subject,
                    status,
                    COALESCE(emails_sent, sent_count, 0) as sent_count,
                    COALESCE(total_recipients, 0) as recipients_count,
                    created_at
                FROM campaigns
                WHERE organization_id = :org_id
                ORDER BY created_at DESC
                LIMIT 5
            """),
            {'org_id': current_user.organization_id}
        )
        
        campaigns = []
        for row in campaigns_result:
            campaigns.append({
                'id': row[0],
                'name': row[1],
                'subject': row[2],
                'status': row[3],
                'sent_count': row[4],
                'recipients_count': row[5],
                'created_at': row[6]
            })
        
        logger.info(f"Dashboard stats: {stats}, Campaigns: {len(campaigns)}")
        
    except Exception as e:
        logger.error(f"Dashboard error: {e}", exc_info=True)
        stats = {'emails_sent': 0, 'total_contacts': 0, 'domains': 0, 'queued': 0}
        campaigns = []
    
    return render_template('dashboard/index.html', stats=stats, campaigns=campaigns)

@dashboard_bp.route('/send-email')
@login_required
def send_email():
    """Send email page"""
    try:
        result = db.session.execute(
            text("SELECT id, domain_name, dns_verified FROM domains WHERE organization_id = :org_id ORDER BY created_at DESC"),
            {'org_id': current_user.organization_id}
        )
        domains = [dict(row._mapping) for row in result]
        return render_template('dashboard/send_email.html', domains=domains)
    except Exception as e:
        logger.error(f"Send email error: {e}", exc_info=True)
        return render_template('dashboard/send_email.html', domains=[])

@dashboard_bp.route('/bulk-send')
@login_required
def bulk_send():
    return send_email()
