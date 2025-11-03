"""
Email Heatmap & Click Analytics
Tracks where users click in emails
"""
import json
from datetime import datetime
from typing import Dict, List
import logging

logger = logging.getLogger(__name__)


class HeatmapTracker:
    """Track and analyze email click patterns"""
    
    def __init__(self, db_session):
        self.db = db_session
    
    def track_click(self, email_id: str, link_url: str, 
                   click_position: Dict = None, user_agent: str = None,
                   ip_address: str = None) -> Dict:
        """
        Track email link click with position data
        click_position: {'x': int, 'y': int} - coordinates where clicked
        """
        from app.models.analytics import EmailClick
        
        click = EmailClick(
            email_id=email_id,
            link_url=link_url,
            click_x=click_position.get('x') if click_position else None,
            click_y=click_position.get('y') if click_position else None,
            user_agent=user_agent,
            ip_address=ip_address,
            clicked_at=datetime.utcnow()
        )
        
        self.db.add(click)
        self.db.commit()
        
        logger.info(f"Tracked click for email {email_id}: {link_url}")
        
        return click.to_dict()
    
    def track_open(self, email_id: str, user_agent: str = None, 
                  ip_address: str = None, location: Dict = None):
        """Track email open"""
        from app.models.analytics import EmailOpen
        from app.models.email import Email
        
        # Check if already opened
        existing = EmailOpen.query.filter_by(email_id=email_id).first()
        
        if not existing:
            email_open = EmailOpen(
                email_id=email_id,
                user_agent=user_agent,
                ip_address=ip_address,
                location=json.dumps(location) if location else None,
                opened_at=datetime.utcnow()
            )
            
            self.db.add(email_open)
            
            # Update email status
            email = Email.query.get(email_id)
            if email and email.status == 'sent':
                email.status = 'opened'
                email.opened_at = datetime.utcnow()
            
            self.db.commit()
            logger.info(f"Tracked open for email {email_id}")
    
    def generate_heatmap(self, campaign_id: str) -> Dict:
        """
        Generate heatmap data for a campaign
        Returns aggregated click positions
        """
        from app.models.analytics import EmailClick
        from app.models.email import Email
        
        # Get all emails in campaign
        emails = Email.query.filter_by(campaign_id=campaign_id).all()
        email_ids = [e.id for e in emails]
        
        # Get all clicks
        clicks = EmailClick.query.filter(
            EmailClick.email_id.in_(email_ids),
            EmailClick.click_x.isnot(None),
            EmailClick.click_y.isnot(None)
        ).all()
        
        # Aggregate click positions
        click_positions = []
        link_clicks = {}
        
        for click in clicks:
            click_positions.append({
                'x': click.click_x,
                'y': click.click_y,
                'timestamp': click.clicked_at.isoformat()
            })
            
            # Count clicks per link
            if click.link_url not in link_clicks:
                link_clicks[click.link_url] = 0
            link_clicks[click.link_url] += 1
        
        return {
            'campaign_id': campaign_id,
            'total_clicks': len(clicks),
            'unique_links': len(link_clicks),
            'click_positions': click_positions,
            'link_performance': [
                {'url': url, 'clicks': count}
                for url, count in sorted(link_clicks.items(), 
                                        key=lambda x: x[1], reverse=True)
            ]
        }
    
    def get_engagement_metrics(self, campaign_id: str) -> Dict:
        """Get detailed engagement metrics"""
        from app.models.email import Email
        from app.models.analytics import EmailOpen, EmailClick
        
        emails = Email.query.filter_by(campaign_id=campaign_id).all()
        email_ids = [e.id for e in emails]
        
        total_sent = len(emails)
        total_opens = EmailOpen.query.filter(
            EmailOpen.email_id.in_(email_ids)
        ).count()
        
        total_clicks = EmailClick.query.filter(
            EmailClick.email_id.in_(email_ids)
        ).count()
        
        unique_clicks = self.db.query(EmailClick.email_id).filter(
            EmailClick.email_id.in_(email_ids)
        ).distinct().count()
        
        # Device breakdown
        device_stats = self._analyze_devices(email_ids)
        
        # Time-based analysis
        time_stats = self._analyze_time_patterns(email_ids)
        
        # Geographic analysis
        geo_stats = self._analyze_geography(email_ids)
        
        return {
            'campaign_id': campaign_id,
            'total_sent': total_sent,
            'total_opens': total_opens,
            'total_clicks': total_clicks,
            'open_rate': round((total_opens / total_sent * 100), 2) if total_sent > 0 else 0,
            'click_rate': round((unique_clicks / total_sent * 100), 2) if total_sent > 0 else 0,
            'click_to_open_rate': round((unique_clicks / total_opens * 100), 2) if total_opens > 0 else 0,
            'devices': device_stats,
            'time_patterns': time_stats,
            'geography': geo_stats
        }
    
    def _analyze_devices(self, email_ids: List[str]) -> Dict:
        """Analyze device types from user agents"""
        from app.models.analytics import EmailOpen
        
        opens = EmailOpen.query.filter(
            EmailOpen.email_id.in_(email_ids),
            EmailOpen.user_agent.isnot(None)
        ).all()
        
        mobile = 0
        desktop = 0
        tablet = 0
        
        for open_record in opens:
            ua = open_record.user_agent.lower()
            if 'mobile' in ua or 'android' in ua or 'iphone' in ua:
                mobile += 1
            elif 'tablet' in ua or 'ipad' in ua:
                tablet += 1
            else:
                desktop += 1
        
        total = mobile + desktop + tablet
        
        return {
            'mobile': {'count': mobile, 'percentage': round(mobile/total*100, 2) if total > 0 else 0},
            'desktop': {'count': desktop, 'percentage': round(desktop/total*100, 2) if total > 0 else 0},
            'tablet': {'count': tablet, 'percentage': round(tablet/total*100, 2) if total > 0 else 0}
        }
    
    def _analyze_time_patterns(self, email_ids: List[str]) -> Dict:
        """Analyze when emails are opened/clicked"""
        from app.models.analytics import EmailOpen
        
        opens = EmailOpen.query.filter(
            EmailOpen.email_id.in_(email_ids)
        ).all()
        
        hourly_stats = {str(i): 0 for i in range(24)}
        daily_stats = {str(i): 0 for i in range(7)}
        
        for open_record in opens:
            hour = open_record.opened_at.hour
            day = open_record.opened_at.weekday()
            
            hourly_stats[str(hour)] += 1
            daily_stats[str(day)] += 1
        
        return {
            'by_hour': hourly_stats,
            'by_day': daily_stats
        }
    
    def _analyze_geography(self, email_ids: List[str]) -> Dict:
        """Analyze geographic distribution"""
        from app.models.analytics import EmailOpen
        
        opens = EmailOpen.query.filter(
            EmailOpen.email_id.in_(email_ids),
            EmailOpen.location.isnot(None)
        ).all()
        
        countries = {}
        cities = {}
        
        for open_record in opens:
            try:
                location = json.loads(open_record.location)
                country = location.get('country', 'Unknown')
                city = location.get('city', 'Unknown')
                
                countries[country] = countries.get(country, 0) + 1
                cities[city] = cities.get(city, 0) + 1
            except:
                pass
        
        return {
            'countries': countries,
            'cities': cities
        }
