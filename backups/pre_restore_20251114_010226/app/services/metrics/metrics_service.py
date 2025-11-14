"""
Metrics Service - System metrics and monitoring
"""
from app import redis_client, db
from app.models.email import Email
from sqlalchemy import func
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class MetricsService:
    """Metrics collection and reporting"""
    
    def get_live_stats(self):
        """Get real-time statistics"""
        try:
            # Redis metrics
            total_sent = int(redis_client.get('metrics:sent:total') or 0)
            total_failed = int(redis_client.get('metrics:failed:total') or 0)
            current_rate = int(redis_client.get('metrics:send_rate:current') or 0)
            
            # Database metrics (last hour)
            one_hour_ago = datetime.utcnow() - timedelta(hours=1)
            
            recent_stats = db.session.query(
                func.count(Email.id).label('total'),
                func.sum(func.cast(Email.bounced, db.Integer)).label('bounced'),
                func.sum(func.cast(Email.opened, db.Integer)).label('opened'),
                func.sum(func.cast(Email.clicked, db.Integer)).label('clicked')
            ).filter(
                Email.created_at >= one_hour_ago
            ).first()
            
            return {
                'total_sent_alltime': total_sent,
                'total_failed_alltime': total_failed,
                'current_send_rate': current_rate,
                'last_hour': {
                    'total': recent_stats.total or 0,
                    'bounced': recent_stats.bounced or 0,
                    'opened': recent_stats.opened or 0,
                    'clicked': recent_stats.clicked or 0
                },
                'timestamp': datetime.utcnow().isoformat()
            }
        
        except Exception as e:
            logger.error(f"Error getting live stats: {e}")
            return {}
    
    def get_hourly_stats(self, hours=24):
        """Get hourly statistics"""
        try:
            stats = []
            now = datetime.utcnow()
            
            for i in range(hours):
                hour_start = now - timedelta(hours=i+1)
                hour_end = now - timedelta(hours=i)
                
                hour_stats = db.session.query(
                    func.count(Email.id).label('total'),
                    func.sum(func.cast(Email.bounced, db.Integer)).label('bounced'),
                    func.sum(func.cast(Email.opened, db.Integer)).label('opened')
                ).filter(
                    Email.created_at >= hour_start,
                    Email.created_at < hour_end
                ).first()
                
                stats.append({
                    'hour': hour_start.strftime('%Y-%m-%d %H:00'),
                    'total': hour_stats.total or 0,
                    'bounced': hour_stats.bounced or 0,
                    'opened': hour_stats.opened or 0
                })
            
            return list(reversed(stats))
        
        except Exception as e:
            logger.error(f"Error getting hourly stats: {e}")
            return []
    
    def get_queue_depths(self):
        """Get current queue depths"""
        try:
            depths = {}
            total = 0
            
            for priority in range(1, 11):
                depth = redis_client.llen(f'outgoing_{priority}')
                depths[f'priority_{priority}'] = depth
                total += depth
            
            depths['total'] = total
            return depths
        
        except Exception as e:
            logger.error(f"Error getting queue depths: {e}")
            return {}
