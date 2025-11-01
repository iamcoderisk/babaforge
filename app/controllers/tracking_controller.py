from flask import Blueprint, request, send_file, redirect, render_template, jsonify
from app import db
from app.models.email import Email
from app.models.email_tracking import EmailOpen, EmailClick, EmailUnsubscribe, EmailBounce
from datetime import datetime
import io
import logging

logger = logging.getLogger(__name__)

tracking_bp = Blueprint('tracking', __name__, url_prefix='/t')

# 1x1 transparent pixel
TRACKING_PIXEL = b'\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x80\x00\x00\xff\xff\xff\x00\x00\x00\x21\xf9\x04\x01\x00\x00\x00\x00\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02\x44\x01\x00\x3b'

@tracking_bp.route('/open/<tracking_id>')
def track_open(tracking_id):
    """Track email open"""
    try:
        email = Email.query.filter_by(tracking_id=tracking_id).first()
        
        if email:
            # Record open event
            email_open = EmailOpen(email_id=email.id)
            email_open.ip_address = request.remote_addr
            email_open.user_agent = request.headers.get('User-Agent', '')
            
            # Update email
            if not email.opened:
                email.opened = True
                email.opened_at = datetime.utcnow()
            
            email.open_count = (email.open_count or 0) + 1
            
            db.session.add(email_open)
            db.session.commit()
            
            logger.info(f"Email {email.id} opened by {email.to_email}")
        
    except Exception as e:
        logger.error(f"Track open error: {e}")
    
    # Return tracking pixel
    return send_file(
        io.BytesIO(TRACKING_PIXEL),
        mimetype='image/gif',
        as_attachment=False
    )

@tracking_bp.route('/click/<tracking_id>')
def track_click(tracking_id):
    """Track email click"""
    url = request.args.get('url', '')
    
    try:
        email = Email.query.filter_by(tracking_id=tracking_id).first()
        
        if email and url:
            # Record click event
            email_click = EmailClick(email_id=email.id, url=url)
            email_click.ip_address = request.remote_addr
            email_click.user_agent = request.headers.get('User-Agent', '')
            
            # Update email click count
            email.click_count = (email.click_count or 0) + 1
            
            db.session.add(email_click)
            db.session.commit()
            
            logger.info(f"Email {email.id} link clicked: {url}")
            
            # Redirect to actual URL
            return redirect(url)
        
    except Exception as e:
        logger.error(f"Track click error: {e}")
    
    # Fallback redirect
    return redirect(url if url else 'https://sendbaba.com')

@tracking_bp.route('/unsubscribe/<tracking_id>', methods=['GET', 'POST'])
def unsubscribe(tracking_id):
    """Handle unsubscribe"""
    email = Email.query.filter_by(tracking_id=tracking_id).first()
    
    if request.method == 'POST':
        reason = request.form.get('reason', '')
        
        try:
            if email:
                # Check if already unsubscribed
                existing = EmailUnsubscribe.query.filter_by(
                    email_address=email.to_email
                ).first()
                
                if not existing:
                    unsubscribe = EmailUnsubscribe(
                        email_address=email.to_email,
                        organization_id=email.organization_id
                    )
                    unsubscribe.reason = reason
                    unsubscribe.ip_address = request.remote_addr
                    
                    db.session.add(unsubscribe)
                    db.session.commit()
                    
                    logger.info(f"Unsubscribe: {email.to_email}")
                
                return render_template('tracking/unsubscribed.html')
            
        except Exception as e:
            logger.error(f"Unsubscribe error: {e}")
            return render_template('tracking/error.html')
    
    return render_template('tracking/unsubscribe.html', email=email)
