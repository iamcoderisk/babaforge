# ============= app/controllers/analytics_controller.py =============
"""
Analytics Controller - Real-time reporting
"""
from flask import Blueprint, request, jsonify, current_app
from datetime import datetime, timedelta

from app.middleware.auth import require_api_key
from app.utils.logger import get_logger

logger = get_logger(__name__)
bp = Blueprint('analytics', __name__)

@bp.route('/realtime', methods=['GET'])
@require_api_key
def get_realtime_stats(org_id: int):
    """Get real-time statistics"""
    try:
        db = current_app.session()
        from app.models.database import EmailOutgoing
        
        # Last hour stats
        one_hour_ago = datetime.utcnow() - timedelta(hours=1)
        
        emails = db.query(EmailOutgoing).filter(
            EmailOutgoing.org_id == org_id,
            EmailOutgoing.created_at >= one_hour_ago
        ).all()
        
        # Calculate metrics
        total = len(emails)
        sent = sum(1 for e in emails if e.status == 'sent')
        delivered = sum(1 for e in emails if e.delivered_at)
        bounced = sum(1 for e in emails if e.bounced_at)
        opened = sum(1 for e in emails if e.opened)
        clicked = sum(1 for e in emails if e.clicked)
        
        return jsonify({
            'timestamp': datetime.utcnow().isoformat(),
            'period': 'last_hour',
            'metrics': {
                'total': total,
                'sent': sent,
                'delivered': delivered,
                'bounced': bounced,
                'opened': opened,
                'clicked': clicked,
                'delivery_rate': (delivered / total * 100) if total > 0 else 0,
                'bounce_rate': (bounced / total * 100) if total > 0 else 0,
                'open_rate': (opened / delivered * 100) if delivered > 0 else 0,
                'click_rate': (clicked / opened * 100) if opened > 0 else 0
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting analytics: {e}")
        return jsonify({'error': str(e)}), 500
