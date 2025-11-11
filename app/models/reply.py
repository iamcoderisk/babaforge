from app import db
from datetime import datetime

class EmailReply(db.Model):
    __tablename__ = 'email_replies'
    
    id = db.Column(db.String(36), primary_key=True)
    email_id = db.Column(db.String(36), db.ForeignKey('emails.id'))
    campaign_id = db.Column(db.String(36), nullable=True)  # Remove FK constraint
    contact_id = db.Column(db.String(36), db.ForeignKey('contacts.id'))
    
    from_email = db.Column(db.String(255))
    to_email = db.Column(db.String(255))
    subject = db.Column(db.String(500))
    body = db.Column(db.Text)
    
    sentiment = db.Column(db.String(20))  # positive, negative, neutral
    intent = db.Column(db.String(50))  # question, complaint, feedback, etc
    
    auto_responded = db.Column(db.Boolean, default=False)
    response_sent_at = db.Column(db.DateTime)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'email_id': self.email_id,
            'campaign_id': self.campaign_id,
            'from_email': self.from_email,
            'subject': self.subject,
            'sentiment': self.sentiment,
            'intent': self.intent,
            'auto_responded': self.auto_responded,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
