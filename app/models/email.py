from app import db
from datetime import datetime
import uuid

class Email(db.Model):
    __tablename__ = 'emails'
    
    id = db.Column(db.String(36), primary_key=True)
    organization_id = db.Column(db.String(36), db.ForeignKey('organizations.id'), nullable=False, index=True)
    domain_id = db.Column(db.String(36), db.ForeignKey('domains.id'))
    
    sender = db.Column(db.String(255), nullable=False, index=True)
    recipient = db.Column(db.String(255), nullable=False, index=True)
    subject = db.Column(db.String(500))
    
    html_body = db.Column(db.Text)
    text_body = db.Column(db.Text)
    
    status = db.Column(db.String(20), default='queued', index=True)
    
    message_id = db.Column(db.String(255), index=True)
    error_message = db.Column(db.Text)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    sent_at = db.Column(db.DateTime)
    
    def __init__(self, organization_id, sender, recipient, subject, **kwargs):
        self.id = str(uuid.uuid4())
        self.organization_id = organization_id
        self.sender = sender
        self.recipient = recipient
        self.subject = subject
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
