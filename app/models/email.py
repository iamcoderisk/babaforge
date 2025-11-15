from app import db
from datetime import datetime

class Email(db.Model):
    __tablename__ = 'emails'
    
    # Exact columns from your database
    id = db.Column(db.String(36), primary_key=True)
    organization_id = db.Column(db.String(36), nullable=False)
    domain_id = db.Column(db.String(36))
    sender = db.Column(db.String(255), nullable=False)
    recipient = db.Column(db.String(255), nullable=False)
    subject = db.Column(db.String(500))
    html_body = db.Column(db.Text)
    text_body = db.Column(db.Text)
    status = db.Column(db.String(20), default='queued')
    message_id = db.Column(db.String(255))
    error_message = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    sent_at = db.Column(db.DateTime)
    workflow_execution_id = db.Column(db.String(36))
    opened_at = db.Column(db.DateTime)
    campaign_id = db.Column(db.String(36))
    from_email = db.Column(db.String(255))
    to_email = db.Column(db.String(255))
    
    def to_dict(self):
        return {
            'id': self.id,
            'from_email': self.from_email or self.sender,
            'to_email': self.to_email or self.recipient,
            'subject': self.subject,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'sent_at': self.sent_at.isoformat() if self.sent_at else None
        }


class EmailTracking(db.Model):
    __tablename__ = 'email_tracking'
    
    id = db.Column(db.String(36), primary_key=True)
    email_id = db.Column(db.String(36), db.ForeignKey('emails.id'), nullable=False)
    event_type = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class EmailClick(db.Model):
    __tablename__ = 'email_clicks'
    
    id = db.Column(db.String(36), primary_key=True)
    email_id = db.Column(db.String(36), db.ForeignKey('emails.id'), nullable=False)
    url = db.Column(db.Text)
    clicked_at = db.Column(db.DateTime, default=datetime.utcnow)


class EmailOpen(db.Model):
    __tablename__ = 'email_opens'
    
    id = db.Column(db.String(36), primary_key=True)
    email_id = db.Column(db.String(36), db.ForeignKey('emails.id'), nullable=False)
    opened_at = db.Column(db.DateTime, default=datetime.utcnow)


class EmailBounce(db.Model):
    __tablename__ = 'email_bounces'
    
    id = db.Column(db.String(36), primary_key=True)
    email_id = db.Column(db.String(36), db.ForeignKey('emails.id'), nullable=False)
    bounce_type = db.Column(db.String(50))
    reason = db.Column(db.Text)
    bounced_at = db.Column(db.DateTime, default=datetime.utcnow)


class EmailUnsubscribe(db.Model):
    __tablename__ = 'email_unsubscribes'
    
    id = db.Column(db.String(36), primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    organization_id = db.Column(db.String(36), db.ForeignKey('organizations.id'))
    unsubscribed_at = db.Column(db.DateTime, default=datetime.utcnow)


class DNSRecord(db.Model):
    __tablename__ = 'dns_records'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    domain = db.Column(db.String(255), nullable=False)
    record_type = db.Column(db.String(10), nullable=False)
    record_name = db.Column(db.String(255), nullable=False)
    record_value = db.Column(db.Text, nullable=False)
    validated = db.Column(db.Boolean, default=False)
    last_checked = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
