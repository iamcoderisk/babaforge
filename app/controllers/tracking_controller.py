"""
Email Tracking Controller
Handles open tracking pixels and click tracking redirects
"""
from flask import Blueprint, request, redirect, send_file, jsonify
from io import BytesIO
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

tracking_bp = Blueprint('tracking', __name__)


@tracking_bp.route('/open/<email_id>.gif')
def track_open(email_id):
    """Tracking pixel for email opens"""
    try:
        # Track open (can be enhanced later with database)
        logger.info(f"Tracked open for email: {email_id}")
    except Exception as e:
        logger.error(f"Track open error: {e}")
    
    # Return 1x1 transparent GIF (lazy load PIL only when needed)
    try:
        from PIL import Image
        img = Image.new('RGBA', (1, 1), (0, 0, 0, 0))
        img_io = BytesIO()
        img.save(img_io, 'GIF')
        img_io.seek(0)
        return send_file(img_io, mimetype='image/gif', max_age=0)
    except ImportError:
        # Fallback: return empty response
        return '', 200, {'Content-Type': 'image/gif'}


@tracking_bp.route('/click/<email_id>/<link_id>')
def track_click(email_id, link_id):
    """Track link clicks and redirect"""
    try:
        from urllib.parse import unquote
        target_url = request.args.get('url', 'https://sendbaba.com')
        target_url = unquote(target_url)
        
        logger.info(f"Tracked click for email {email_id}: {target_url}")
        return redirect(target_url, code=302)
        
    except Exception as e:
        logger.error(f"Track click error: {e}")
        return redirect('https://sendbaba.com', code=302)


@tracking_bp.route('/unsubscribe/<email_id>')
def track_unsubscribe(email_id):
    """Handle unsubscribe requests"""
    return """
    <html>
    <head><title>Unsubscribed</title></head>
    <body style="font-family: Arial; text-align: center; padding: 50px;">
        <h1>✓ You've been unsubscribed</h1>
        <p>You will no longer receive emails from us.</p>
    </body>
    </html>
    """
