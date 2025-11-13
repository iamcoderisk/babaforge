from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
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
        emails_sent = db.session.execute(
            text("SELECT COUNT(*) FROM campaigns WHERE organization_id = :org_id AND created_at >= date_trunc('month', CURRENT_DATE)"),
            {'org_id': current_user.organization_id}
        ).scalar() or 0
        
        total_contacts = db.session.execute(
            text("SELECT COUNT(*) FROM contacts WHERE organization_id = :org_id"),
            {'org_id': current_user.organization_id}
        ).scalar() or 0
        
        domains_count = db.session.execute(
            text("SELECT COUNT(*) FROM domains WHERE organization_id = :org_id"),
            {'org_id': current_user.organization_id}
        ).scalar() or 0
        
        stats = {
            'emails_sent': emails_sent,
            'total_contacts': total_contacts,
            'domains': domains_count,
            'queued': 0
        }
        
        campaigns_result = db.session.execute(
            text("""
                SELECT id, name, subject, status,
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
                'id': row[0], 'name': row[1], 'subject': row[2], 'status': row[3],
                'sent_count': row[4], 'recipients_count': row[5], 'created_at': row[6]
            })
        
    except Exception as e:
        logger.error(f"Dashboard error: {e}", exc_info=True)
        stats = {'emails_sent': 0, 'total_contacts': 0, 'domains': 0, 'queued': 0}
        campaigns = []
    
    return render_template('dashboard/index.html', stats=stats, campaigns=campaigns)

@dashboard_bp.route('/send-email', methods=['GET', 'POST'])
@login_required
def send_email():
    """Send single email"""
    if request.method == 'POST':
        try:
            to_email = request.form.get('to_email')
            subject = request.form.get('subject')
            message = request.form.get('message')
            from_email_prefix = request.form.get('from_email', 'noreply')
            from_domain = request.form.get('from_domain', 'sendbaba.com')
            
            # Build full from email
            from_email = f"{from_email_prefix}@{from_domain}"
            
            logger.info(f"📧 Sending to {to_email} from {from_email}")
            
            if not to_email or not subject or not message:
                flash('❌ Please fill all fields', 'danger')
                return redirect(url_for('dashboard.send_email'))
            
            from app.services.email_service import send_email as send_email_service
            
            result = send_email_service(
                to_email=to_email,
                subject=subject,
                body=message,
                from_email=from_email,
                from_name=from_domain,
                organization_id=current_user.organization_id
            )
            
            if result:
                flash(f'✅ Email sent to {to_email} from {from_email}!', 'success')
            else:
                flash('❌ Failed to send email.', 'danger')
                
        except Exception as e:
            logger.error(f"Send email error: {e}", exc_info=True)
            flash(f'❌ Error: {str(e)}', 'danger')
        
        return redirect(url_for('dashboard.send_email'))
    
    # GET - show form
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
    return send_email()
