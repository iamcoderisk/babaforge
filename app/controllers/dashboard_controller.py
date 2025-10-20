"""
Dashboard Controller - Live Reporting
"""
from flask import Blueprint, render_template, jsonify
from app import redis_client, db
from app.models.email import Email
from sqlalchemy import func
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/')
def index():
    """Main dashboard page"""
    return render_template('dashboard/index.html')

@dashboard_bp.route('/live-stats')
def live_stats():
    """Get live statistics"""
    try:
        # Get from Redis
        total_sent = redis_client.get('metrics:sent:total') or 0
        total_failed = redis_client.get('metrics:failed:total') or 0
        current_rate = redis_client.get('metrics:send_rate:current') or 0
        
        # Get queue depths
        total_queued = 0
        for priority in range(1, 11):
            depth = redis_client.llen(f'outgoing_{priority}')
            total_queued += depth
        
        return jsonify({
            'success': True,
            'stats': {
                'total_sent_alltime': int(total_sent),
                'total_failed_alltime': int(total_failed),
                'current_send_rate': int(current_rate),
                'total_queued': total_queued,
                'last_hour': {
                    'total': 0,
                    'bounced': 0,
                    'opened': 0,
                    'clicked': 0
                },
                'timestamp': datetime.utcnow().isoformat()
            }
        })
    except Exception as e:
        logger.error(f"Error getting live stats: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@dashboard_bp.route('/hourly-stats')
def hourly_stats():
    """Get hourly statistics"""
    try:
        # Return sample data for now
        stats = []
        for i in range(24):
            hour = datetime.utcnow() - timedelta(hours=i)
            stats.append({
                'hour': hour.strftime('%Y-%m-%d %H:00'),
                'total': 0,
                'bounced': 0,
                'opened': 0
            })
        
        return jsonify({
            'success': True,
            'stats': list(reversed(stats))
        })
    except Exception as e:
        logger.error(f"Error getting hourly stats: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@dashboard_bp.route('/queue-depth')
def queue_depth():
    """Get current queue depths"""
    try:
        depths = {}
        total = 0
        
        for priority in range(1, 11):
            depth = redis_client.llen(f'outgoing_{priority}')
            depths[f'priority_{priority}'] = depth
            total += depth
        
        depths['total'] = total
        
        return jsonify({
            'success': True,
            'queues': depths
        })
    except Exception as e:
        logger.error(f"Error getting queue depths: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@dashboard_bp.route('/domain-stats')
def domain_stats():
    """Get domain statistics"""
    try:
        # Return empty for now until we have data
        return jsonify({
            'success': True,
            'domains': []
        })
    except Exception as e:
        logger.error(f"Error getting domain stats: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@dashboard_bp.route('/ip-stats')
def ip_stats():
    """Get IP statistics"""
    try:
        # Return empty for now until we have data
        return jsonify({
            'success': True,
            'ips': []
        })
    except Exception as e:
        logger.error(f"Error getting IP stats: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
