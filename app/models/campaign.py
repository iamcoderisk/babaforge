from app import db
from datetime import datetime

class Campaign(db.Model):
    __tablename__ = 'campaigns'
    
    id = db.Column(db.String(36), primary_key=True)
    organization_id = db.Column(db.String(36), db.ForeignKey('organizations.id'), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    subject = db.Column(db.String(500))
    from_email = db.Column(db.String(255))
    status = db.Column(db.String(20), default='draft')
    
    emails_sent = db.Column(db.Integer, default=0)
    sent_count = db.Column(db.Integer, default=0)
    total_recipients = db.Column(db.Integer, default=0)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'subject': self.subject,
            'status': self.status,
            'total_sent': self.emails_sent or self.sent_count or 0,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class CampaignRecipient(db.Model):
    __tablename__ = 'campaign_recipients'
    
    id = db.Column(db.String(36), primary_key=True)
    campaign_id = db.Column(db.String(36), db.ForeignKey('campaigns.id'), nullable=False)
    contact_id = db.Column(db.String(36), db.ForeignKey('contacts.id'), nullable=False)
    status = db.Column(db.String(20), default='pending')
    sent_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class CampaignAnalytics(db.Model):
    __tablename__ = 'campaign_analytics'
    
    id = db.Column(db.String(36), primary_key=True)
    campaign_id = db.Column(db.String(36), db.ForeignKey('campaigns.id'), nullable=False)
    metric_name = db.Column(db.String(100))
    metric_value = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
