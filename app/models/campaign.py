from app import db
from datetime import datetime
import uuid

class Campaign(db.Model):
    __tablename__ = 'campaigns'
    
    id = db.Column(db.String(36), primary_key=True)
    organization_id = db.Column(db.String(36), db.ForeignKey('organizations.id'), nullable=False, index=True)
    
    name = db.Column(db.String(200), nullable=False)
    subject = db.Column(db.String(500))
    from_email = db.Column(db.String(255))
    from_name = db.Column(db.String(200))
    reply_to = db.Column(db.String(255))
    
    # Content
    html_body = db.Column(db.Text)
    text_body = db.Column(db.Text)
    template_id = db.Column(db.String(36), db.ForeignKey('email_templates.id'))
    
    # Targeting
    segment_filters = db.Column(db.JSON)  # Filters for selecting contacts
    
    # Status
    status = db.Column(db.String(20), default='draft', index=True)  # draft, scheduled, sending, sent, paused, cancelled
    
    # Stats
    total_recipients = db.Column(db.Integer, default=0)
    emails_sent = db.Column(db.Integer, default=0)
    emails_delivered = db.Column(db.Integer, default=0)
    emails_opened = db.Column(db.Integer, default=0)
    emails_clicked = db.Column(db.Integer, default=0)
    emails_bounced = db.Column(db.Integer, default=0)
    emails_complained = db.Column(db.Integer, default=0)
    emails_unsubscribed = db.Column(db.Integer, default=0)
    
    # Scheduling
    scheduled_at = db.Column(db.DateTime)
    started_at = db.Column(db.DateTime)
    completed_at = db.Column(db.DateTime)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __init__(self, organization_id, name, **kwargs):
        self.id = str(uuid.uuid4())
        self.organization_id = organization_id
        self.name = name
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    @property
    def open_rate(self):
        if self.emails_delivered > 0:
            return round((self.emails_opened / self.emails_delivered) * 100, 2)
        return 0
    
    @property
    def click_rate(self):
        if self.emails_delivered > 0:
            return round((self.emails_clicked / self.emails_delivered) * 100, 2)
        return 0
    
    @property
    def bounce_rate(self):
        if self.emails_sent > 0:
            return round((self.emails_bounced / self.emails_sent) * 100, 2)
        return 0
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'subject': self.subject,
            'from_email': self.from_email,
            'from_name': self.from_name,
            'reply_to': self.reply_to,
            'status': self.status,
            'stats': {
                'total_recipients': self.total_recipients,
                'emails_sent': self.emails_sent,
                'emails_delivered': self.emails_delivered,
                'emails_opened': self.emails_opened,
                'emails_clicked': self.emails_clicked,
                'emails_bounced': self.emails_bounced,
                'emails_complained': self.emails_complained,
                'emails_unsubscribed': self.emails_unsubscribed,
                'open_rate': self.open_rate,
                'click_rate': self.click_rate,
                'bounce_rate': self.bounce_rate
            },
            'scheduled_at': self.scheduled_at.isoformat() if self.scheduled_at else None,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class CampaignRecipient(db.Model):
    __tablename__ = 'campaign_recipients'
    
    id = db.Column(db.String(36), primary_key=True)
    campaign_id = db.Column(db.String(36), db.ForeignKey('campaigns.id'), nullable=False, index=True)
    contact_id = db.Column(db.String(36), db.ForeignKey('contacts.id'), nullable=False, index=True)
    email_id = db.Column(db.String(36), db.ForeignKey('emails.id'))
    
    # Status
    status = db.Column(db.String(20), default='pending')  # pending, sent, failed, bounced, opened, clicked
    
    # Tracking
    sent_at = db.Column(db.DateTime)
    opened_at = db.Column(db.DateTime)
    clicked_at = db.Column(db.DateTime)
    bounced_at = db.Column(db.DateTime)
    
    # Error info
    error_message = db.Column(db.Text)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __init__(self, campaign_id, contact_id):
        self.id = str(uuid.uuid4())
        self.campaign_id = campaign_id
        self.contact_id = contact_id
