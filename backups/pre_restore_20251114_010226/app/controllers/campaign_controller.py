from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app import db
from sqlalchemy import text
import logging

logger = logging.getLogger(__name__)

campaign_bp = Blueprint('campaigns', __name__)

@campaign_bp.route('/campaigns')
@campaign_bp.route('/dashboard/campaigns')
@login_required
def list_campaigns():
    """List all campaigns with correct metrics"""
    try:
        result = db.session.execute(
            text("""
                SELECT 
                    id,
                    name,
                    subject,
                    status,
                    COALESCE(emails_sent, sent_count, 0) as total_sent,
                    COALESCE(total_recipients, 0) as recipients_count,
                    created_at
                FROM campaigns 
                WHERE organization_id = :org_id 
                ORDER BY created_at DESC
            """),
            {'org_id': current_user.organization_id}
        )
        
        campaigns = []
        for row in result:
            campaigns.append({
                'id': row[0],
                'name': row[1],
                'subject': row[2],
                'status': row[3],
                'total_sent': row[4],
                'recipients_count': row[5],
                'created_at': row[6]
            })
        
        logger.info(f"Found {len(campaigns)} campaigns for org {current_user.organization_id}")
        
        return render_template('dashboard/campaigns.html', campaigns=campaigns)
        
    except Exception as e:
        logger.error(f"List campaigns error: {e}", exc_info=True)
        return render_template('dashboard/campaigns.html', campaigns=[])

@campaign_bp.route('/campaigns/create')
@campaign_bp.route('/dashboard/campaigns/create')
@login_required
def create_campaign():
    """Redirect to send email"""
    return redirect(url_for('dashboard.send_email'))

@campaign_bp.route('/campaigns/<campaign_id>')
@campaign_bp.route('/dashboard/campaigns/<campaign_id>')
@login_required
def view_campaign(campaign_id):
    """View campaign details"""
    try:
        result = db.session.execute(
            text("""
                SELECT 
                    id,
                    name,
                    subject,
                    status,
                    COALESCE(emails_sent, sent_count, 0) as sent_count,
                    COALESCE(emails_opened, opened_count, 0) as opened_count,
                    COALESCE(emails_clicked, clicked_count, 0) as clicked_count,
                    COALESCE(emails_bounced, bounced_count, 0) as bounced_count,
                    COALESCE(total_recipients, 0) as recipients_count,
                    created_at,
                    started_at,
                    completed_at
                FROM campaigns 
                WHERE id = :id AND organization_id = :org_id
            """),
            {'id': campaign_id, 'org_id': current_user.organization_id}
        )
        
        row = result.fetchone()
        
        if not row:
            flash('Campaign not found', 'error')
            return redirect(url_for('campaigns.list_campaigns'))
        
        campaign = {
            'id': row[0],
            'name': row[1],
            'subject': row[2],
            'status': row[3],
            'sent_count': row[4],
            'opened_count': row[5],
            'clicked_count': row[6],
            'bounced_count': row[7],
            'recipients_count': row[8],
            'created_at': row[9],
            'started_at': row[10],
            'completed_at': row[11]
        }
        
        return render_template('dashboard/campaigns/view.html', campaign=campaign)
        
    except Exception as e:
        logger.error(f"View campaign error: {e}", exc_info=True)
        flash('Error loading campaign', 'error')
        return redirect(url_for('campaigns.list_campaigns'))
