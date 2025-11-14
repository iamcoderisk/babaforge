from app import db
from datetime import datetime
import uuid

class EmailOpen(db.Model):
    __tablename__ = 'email_opens'
    
    id = db.Column(db.String(36), primary_key=True)
    email_id = db.Column(db.String(36), db.ForeignKey('emails.id'), nullable=False)
    
    # Tracking data
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.Text)
    opened_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Geolocation
    country = db.Column(db.String(100))
    city = db.Column(db.String(100))
    
    def __init__(self, email_id):
        self.id = str(uuid.uuid4())
        self.email_id = email_id

class EmailClick(db.Model):
    __tablename__ = 'email_clicks'
    
    id = db.Column(db.String(36), primary_key=True)
    email_id = db.Column(db.String(36), db.ForeignKey('emails.id'), nullable=False)
    
    # Click data
    url = db.Column(db.Text, nullable=False)
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.Text)
    clicked_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Geolocation
    country = db.Column(db.String(100))
    city = db.Column(db.String(100))
    
    def __init__(self, email_id, url):
        self.id = str(uuid.uuid4())
        self.email_id = email_id
        self.url = url

class EmailUnsubscribe(db.Model):
    __tablename__ = 'email_unsubscribes'
    
    id = db.Column(db.String(36), primary_key=True)
    email_address = db.Column(db.String(255), nullable=False, unique=True)
    organization_id = db.Column(db.String(36), db.ForeignKey('organizations.id'))
    
    # Unsubscribe data
    reason = db.Column(db.String(255))
    ip_address = db.Column(db.String(45))
    unsubscribed_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __init__(self, email_address, organization_id=None):
        self.id = str(uuid.uuid4())
        self.email_address = email_address
        self.organization_id = organization_id

class EmailBounce(db.Model):
    __tablename__ = 'email_bounces'
    
    id = db.Column(db.String(36), primary_key=True)
    email_id = db.Column(db.String(36), db.ForeignKey('emails.id'), nullable=False)
    
    # Bounce data
    bounce_type = db.Column(db.String(50))  # hard, soft
    reason = db.Column(db.Text)
    bounced_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __init__(self, email_id):
        self.id = str(uuid.uuid4())
        self.email_id = email_id
