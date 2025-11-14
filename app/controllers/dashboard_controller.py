from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from app import db, redis_client
from sqlalchemy import text
import logging

logger = logging.getLogger(__name__)

dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/dashboard')

@dashboard_bp.route('/')
@login_required
def index():
    """Dashboard with real stats"""
    try:
        # Get emails sent this month
        emails_sent_result = db.session.execute(
            text("""
                SELECT COUNT(*) 
                FROM emails 
                WHERE organization_id = :org_id 
                AND status = 'sent'
                AND created_at >= date_trunc('month', CURRENT_DATE)
            """),
            {'org_id': current_user.organization_id}
        )
        emails_sent = emails_sent_result.scalar() or 0
        
        # Get total contacts
        contacts_result = db.session.execute(
            text("SELECT COUNT(*) FROM contacts WHERE organization_id = :org_id"),
            {'org_id': current_user.organization_id}
        )
        total_contacts = contacts_result.scalar() or 0
        
        # Get domains count
        domains_result = db.session.execute(
            text("SELECT COUNT(*) FROM domains WHERE organization_id = :org_id"),
            {'org_id': current_user.organization_id}
        )
        domains_count = domains_result.scalar() or 0
        
        # Get queued emails from Redis
        queued = 0
        try:
            for priority in range(1, 11):
                queue_length = redis_client.llen(f'outgoing_{priority}')
                queued += queue_length if queue_length else 0
        except Exception as redis_error:
            logger.warning(f"Redis queue check failed: {redis_error}")
            queued = 0
        
        stats = {
            'emails_sent': int(emails_sent),
            'total_contacts': int(total_contacts),
            'domains': int(domains_count),
            'queued': int(queued)
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
        
        logger.info(f"Dashboard stats for org {current_user.organization_id}: {stats}")
        logger.info(f"Campaigns count: {len(campaigns)}")
        
    except Exception as e:
        logger.error(f"Dashboard error: {e}", exc_info=True)
        stats = {
            'emails_sent': 0,
            'total_contacts': 0,
            'domains': 0,
            'queued': 0
        }
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
        logger.error(f"Send email page error: {e}", exc_info=True)
        return render_template('dashboard/send_email.html', domains=[])

@dashboard_bp.route('/bulk-send')
@login_required
def bulk_send():
    """Bulk send page"""
    try:
        # Get domains
        domains_result = db.session.execute(
            text("SELECT id, domain_name, dns_verified FROM domains WHERE organization_id = :org_id"),
            {'org_id': current_user.organization_id}
        )
        domains = [dict(row._mapping) for row in domains_result]
        
        # Get contacts
        contacts_result = db.session.execute(
            text("SELECT id, email, name FROM contacts WHERE organization_id = :org_id ORDER BY created_at DESC"),
            {'org_id': current_user.organization_id}
        )
        contacts = [dict(row._mapping) for row in contacts_result]
        
        return render_template('dashboard/bulk_send.html', domains=domains, contacts=contacts)
    except Exception as e:
        logger.error(f"Bulk send page error: {e}", exc_info=True)
        return render_template('dashboard/bulk_send.html', domains=[], contacts=[])
