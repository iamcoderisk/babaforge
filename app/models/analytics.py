"""
Advanced Analytics Models
"""
from app import db
from datetime import datetime
import uuid


class EmailOpen(db.Model):
    __tablename__ = 'email_opens'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email_id = db.Column(db.String(36), db.ForeignKey('emails.id'), nullable=False, index=True)
    
    user_agent = db.Column(db.String(500))
    ip_address = db.Column(db.String(45))
    location = db.Column(db.Text)  # JSON: {country, city, lat, lng}
    
    opened_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'email_id': self.email_id,
            'ip_address': self.ip_address,
            'opened_at': self.opened_at.isoformat() if self.opened_at else None
        }


class EmailClick(db.Model):
    __tablename__ = 'email_clicks'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email_id = db.Column(db.String(36), db.ForeignKey('emails.id'), nullable=False, index=True)
    
    link_url = db.Column(db.Text, nullable=False)
    link_text = db.Column(db.String(500))
    
    # Heatmap coordinates
    click_x = db.Column(db.Integer)
    click_y = db.Column(db.Integer)
    
    user_agent = db.Column(db.String(500))
    ip_address = db.Column(db.String(45))
    
    clicked_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'email_id': self.email_id,
            'link_url': self.link_url,
            'click_x': self.click_x,
            'click_y': self.click_y,
            'clicked_at': self.clicked_at.isoformat() if self.clicked_at else None
        }


class CampaignAnalytics(db.Model):
    __tablename__ = 'campaign_analytics'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    campaign_id = db.Column(db.String(36), db.ForeignKey('campaigns.id'), nullable=False, unique=True)
    
    # Aggregated stats (updated periodically)
    total_sent = db.Column(db.Integer, default=0)
    total_delivered = db.Column(db.Integer, default=0)
    total_bounced = db.Column(db.Integer, default=0)
    total_opened = db.Column(db.Integer, default=0)
    total_clicked = db.Column(db.Integer, default=0)
    total_unsubscribed = db.Column(db.Integer, default=0)
    total_complained = db.Column(db.Integer, default=0)
    
    # Calculated rates
    delivery_rate = db.Column(db.Float, default=0.0)
    open_rate = db.Column(db.Float, default=0.0)
    click_rate = db.Column(db.Float, default=0.0)
    bounce_rate = db.Column(db.Float, default=0.0)
    
    # Device breakdown (JSON)
    device_stats = db.Column(db.Text)
    
    last_updated = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'campaign_id': self.campaign_id,
            'total_sent': self.total_sent,
            'total_opened': self.total_opened,
            'total_clicked': self.total_clicked,
            'open_rate': self.open_rate,
            'click_rate': self.click_rate,
            'last_updated': self.last_updated.isoformat() if self.last_updated else None
        }
