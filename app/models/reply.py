from app import db
from datetime import datetime

class EmailReply(db.Model):
    __tablename__ = 'email_replies'
    
    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.Integer, db.ForeignKey('organizations.id'))
    campaign_id = db.Column(db.Integer, db.ForeignKey('campaigns.id'), nullable=True)
    contact_id = db.Column(db.Integer, db.ForeignKey('contacts.id'), nullable=True)
    
    # Email details
    from_email = db.Column(db.String(255), nullable=False)
    from_name = db.Column(db.String(255))
    subject = db.Column(db.Text)
    text_body = db.Column(db.Text)
    html_body = db.Column(db.Text)
    message_id = db.Column(db.String(500))
    in_reply_to = db.Column(db.String(500))
    
    # AI Analysis
    sentiment = db.Column(db.String(50))  # positive, negative, neutral
    sentiment_score = db.Column(db.Float)
    intent = db.Column(db.String(100))  # question, interested, not_interested, support
    category = db.Column(db.String(100))  # pricing, demo, features, support, general
    urgency = db.Column(db.String(50))  # high, medium, low
    
    # Response tracking
    responded = db.Column(db.Boolean, default=False)
    responded_at = db.Column(db.DateTime)
    response_text = db.Column(db.Text)
    auto_responded = db.Column(db.Boolean, default=False)
    
    # Metadata
    raw_email = db.Column(db.Text)  # Store original email
    ip_address = db.Column(db.String(50))
    user_agent = db.Column(db.String(500))
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    organization = db.relationship('Organization', backref='email_replies')
    campaign = db.relationship('Campaign', backref='replies')
    contact = db.relationship('Contact', backref='replies')

class ReplyTemplate(db.Model):
    __tablename__ = 'reply_templates'
    
    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.Integer, db.ForeignKey('organizations.id'))
    
    name = db.Column(db.String(255), nullable=False)
    category = db.Column(db.String(100))  # pricing, demo, features, etc.
    subject = db.Column(db.String(500))
    body = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    auto_send = db.Column(db.Boolean, default=False)
    
    # Usage stats
    times_used = db.Column(db.Integer, default=0)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    organization = db.relationship('Organization', backref='reply_templates')

class ReplyRule(db.Model):
    __tablename__ = 'reply_rules'
    
    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.Integer, db.ForeignKey('organizations.id'))
    
    name = db.Column(db.String(255))
    trigger_keywords = db.Column(db.JSON)  # List of keywords to match
    trigger_category = db.Column(db.String(100))
    trigger_sentiment = db.Column(db.String(50))
    
    action = db.Column(db.String(50))  # auto_reply, notify, tag
    template_id = db.Column(db.Integer, db.ForeignKey('reply_templates.id'))
    notify_email = db.Column(db.String(255))
    
    is_active = db.Column(db.Boolean, default=True)
    priority = db.Column(db.Integer, default=0)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    organization = db.relationship('Organization')
    template = db.relationship('ReplyTemplate')
