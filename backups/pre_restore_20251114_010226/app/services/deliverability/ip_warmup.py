"""
IP Warmup Service
Gradually increase sending volume to build sender reputation
"""
from datetime import datetime, timedelta
from typing import Dict
import logging

logger = logging.getLogger(__name__)


class IPWarmup:
    """Manage IP warmup schedule"""
    
    # Standard warmup schedule (days: max emails)
    WARMUP_SCHEDULE = {
        1: 50,
        2: 100,
        3: 200,
        4: 500,
        5: 1000,
        6: 2000,
        7: 5000,
        14: 10000,
        21: 20000,
        28: 50000,
        35: 100000,
        42: -1  # Unlimited
    }
    
    def __init__(self, db_session, organization_id: str):
        self.db = db_session
        self.organization_id = organization_id
    
    def get_current_limit(self) -> Dict:
        """Get current sending limit based on warmup schedule"""
        from app.models.organization import Organization
        
        org = Organization.query.get(self.organization_id)
        
        if not org or not org.warmup_start_date:
            return {
                'status': 'not_started',
                'daily_limit': 50,
                'message': 'IP warmup not started. Starting with conservative limit.'
            }
        
        # Calculate days since warmup started
        days_elapsed = (datetime.utcnow() - org.warmup_start_date).days
        
        # Find appropriate limit
        daily_limit = 50
        for day, limit in sorted(self.WARMUP_SCHEDULE.items()):
            if days_elapsed >= day:
                daily_limit = limit
        
        # Check today's sent count
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        from app.models.email import Email
        
        sent_today = Email.query.filter(
            Email.organization_id == self.organization_id,
            Email.sent_at >= today_start,
            Email.status == 'sent'
        ).count()
        
        remaining = daily_limit - sent_today if daily_limit > 0 else -1
        
        return {
            'status': 'active' if daily_limit > 0 else 'complete',
            'days_elapsed': days_elapsed,
            'daily_limit': daily_limit,
            'sent_today': sent_today,
            'remaining_today': remaining if remaining > 0 else 0,
            'warmup_complete': daily_limit == -1,
            'next_increase': self._get_next_increase(days_elapsed)
        }
    
    def can_send(self, count: int = 1) -> Dict:
        """Check if organization can send given number of emails"""
        limit_info = self.get_current_limit()
        
        if limit_info['warmup_complete']:
            return {
                'allowed': True,
                'reason': 'Warmup complete'
            }
        
        remaining = limit_info.get('remaining_today', 0)
        
        if remaining >= count:
            return {
                'allowed': True,
                'remaining': remaining
            }
        
        return {
            'allowed': False,
            'reason': f'Daily limit reached. {remaining} emails remaining today.',
            'next_reset': 'Tomorrow at midnight',
            'current_limit': limit_info['daily_limit']
        }
    
    def start_warmup(self):
        """Start IP warmup for organization"""
        from app.models.organization import Organization
        
        org = Organization.query.get(self.organization_id)
        if org:
            org.warmup_start_date = datetime.utcnow()
            self.db.commit()
            logger.info(f"Started IP warmup for org {self.organization_id}")
    
    def _get_next_increase(self, days_elapsed: int) -> Dict:
        """Get info about next limit increase"""
        for day, limit in sorted(self.WARMUP_SCHEDULE.items()):
            if day > days_elapsed:
                return {
                    'days_until': day - days_elapsed,
                    'new_limit': limit
                }
        
        return {
            'days_until': 0,
            'new_limit': -1,
            'message': 'Warmup complete'
        }
