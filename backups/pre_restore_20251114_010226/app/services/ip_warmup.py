"""
IP Warmup Service
Gradually increase sending volume to build IP reputation
"""
from datetime import datetime, timedelta
from app import db

class IPWarmupService:
    """Manage IP warmup schedules"""
    
    # Standard warmup schedule (days: max emails)
    WARMUP_SCHEDULE = {
        1: 50,
        2: 100,
        3: 200,
        4: 400,
        5: 800,
        6: 1600,
        7: 3200,
        8: 6400,
        9: 12800,
        10: 25000,
        11: 50000,
        12: 100000,
        13: 200000,
        14: 500000,  # Full volume after 2 weeks
    }
    
    def __init__(self, organization_id):
        self.organization_id = organization_id
    
    def start_warmup(self, ip_address, start_date=None):
        """Start IP warmup process"""
        if not start_date:
            start_date = datetime.utcnow().date()
        
        from app.models.ip_warmup import IPWarmup
        
        warmup = IPWarmup(
            organization_id=self.organization_id,
            ip_address=ip_address,
            start_date=start_date,
            current_day=1,
            status='active'
        )
        
        db.session.add(warmup)
        db.session.commit()
        
        return warmup
    
    def get_daily_limit(self, warmup):
        """Get today's sending limit"""
        if warmup.status != 'active':
            return float('inf')  # No limit if not in warmup
        
        return self.WARMUP_SCHEDULE.get(warmup.current_day, 500000)
    
    def get_current_usage(self, warmup):
        """Get emails sent today"""
        from app.models.email import Email
        
        today = datetime.utcnow().date()
        
        count = Email.query.filter(
            Email.organization_id == self.organization_id,
            db.func.date(Email.created_at) == today
        ).count()
        
        return count
    
    def can_send_email(self, warmup):
        """Check if we can send more emails today"""
        if not warmup or warmup.status != 'active':
            return True
        
        daily_limit = self.get_daily_limit(warmup)
        current_usage = self.get_current_usage(warmup)
        
        return current_usage < daily_limit
    
    def update_warmup_day(self):
        """Update warmup day (run daily)"""
        from app.models.ip_warmup import IPWarmup
        
        active_warmups = IPWarmup.query.filter_by(
            organization_id=self.organization_id,
            status='active'
        ).all()
        
        for warmup in active_warmups:
            days_elapsed = (datetime.utcnow().date() - warmup.start_date).days + 1
            
            warmup.current_day = days_elapsed
            
            # Complete warmup after 14 days
            if days_elapsed >= 14:
                warmup.status = 'completed'
                warmup.completed_at = datetime.utcnow()
        
        db.session.commit()
    
    def get_warmup_progress(self, warmup):
        """Get warmup progress"""
        if not warmup:
            return None
        
        total_days = 14
        progress_percent = min(100, (warmup.current_day / total_days) * 100)
        
        return {
            'current_day': warmup.current_day,
            'total_days': total_days,
            'progress_percent': round(progress_percent, 1),
            'daily_limit': self.get_daily_limit(warmup),
            'current_usage': self.get_current_usage(warmup),
            'status': warmup.status
        }

# Create IP Warmup model
