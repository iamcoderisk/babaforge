"""
Email Model
"""
from datetime import datetime
from app import db

class Email(db.Model):
    """Email model for tracking sent emails"""
    __tablename__ = 'emails'
    
    id = db.Column(db.String(36), primary_key=True)
    batch_id = db.Column(db.String(36), index=True)
    
    # Email details
    recipient = db.Column(db.String(255), nullable=False, index=True)
    sender = db.Column(db.String(255), nullable=False)
    subject = db.Column(db.Text)
    
    # Status
    status = db.Column(db.String(20), default='queued', index=True)
    priority = db.Column(db.Integer, default=5, index=True)
    
    # Metadata
    ip_address = db.Column(db.String(45))
    domain = db.Column(db.String(255), index=True)
    
    # Tracking
    opened = db.Column(db.Boolean, default=False)
    clicked = db.Column(db.Boolean, default=False)
    bounced = db.Column(db.Boolean, default=False)
    bounce_type = db.Column(db.String(20))
    complaint = db.Column(db.Boolean, default=False)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    queued_at = db.Column(db.DateTime)
    sent_at = db.Column(db.DateTime, index=True)
    delivered_at = db.Column(db.DateTime)
    opened_at = db.Column(db.DateTime)
    clicked_at = db.Column(db.DateTime)
    bounced_at = db.Column(db.DateTime)
    
    # Retry
    retry_count = db.Column(db.Integer, default=0)
    last_error = db.Column(db.Text)
    
    def __repr__(self):
        return f'<Email {self.id} to {self.recipient}>'
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'batch_id': self.batch_id,
            'recipient': self.recipient,
            'sender': self.sender,
            'subject': self.subject,
            'status': self.status,
            'priority': self.priority,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'sent_at': self.sent_at.isoformat() if self.sent_at else None,
            'opened': self.opened,
            'clicked': self.clicked,
            'bounced': self.bounced
        }

class IPAddress(db.Model):
    """IP Address model for pool management"""
    __tablename__ = 'ip_addresses'
    
    id = db.Column(db.Integer, primary_key=True)
    ip = db.Column(db.String(45), unique=True, nullable=False)
    hostname = db.Column(db.String(255))
    
    # Status
    active = db.Column(db.Boolean, default=True)
    warmup_stage = db.Column(db.Integer, default=0)
    daily_limit = db.Column(db.Integer, default=1000)
    
    # Reputation
    reputation_score = db.Column(db.Float, default=100.0)
    
    # Tracking
    total_sent = db.Column(db.Integer, default=0)
    total_bounced = db.Column(db.Integer, default=0)
    total_complaints = db.Column(db.Integer, default=0)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_used_at = db.Column(db.DateTime)
    
    def __repr__(self):
        return f'<IPAddress {self.ip}>'

class DNSRecord(db.Model):
    """DNS Record model for tracking domain configuration"""
    __tablename__ = 'dns_records'
    
    id = db.Column(db.Integer, primary_key=True)
    domain = db.Column(db.String(255), nullable=False, index=True)
    record_type = db.Column(db.String(10), nullable=False)  # DKIM, SPF, MX, PTR, DMARC
    record_name = db.Column(db.String(255))
    record_value = db.Column(db.Text)
    
    # Validation
    validated = db.Column(db.Boolean, default=False)
    last_checked = db.Column(db.DateTime)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<DNSRecord {self.record_type} for {self.domain}>'
