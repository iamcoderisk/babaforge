"""
Suppression List Model
Stores bounced, unsubscribed, and complained emails
"""
from app import db
from datetime import datetime
import uuid


class SuppressionList(db.Model):
    __tablename__ = 'suppression_list'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = db.Column(db.String(255), nullable=False, index=True, unique=True)
    type = db.Column(db.String(20), nullable=False)  # hard_bounce, soft_bounce, spam, unsubscribe, complaint
    reason = db.Column(db.Text)
    added_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Metadata
    bounce_count = db.Column(db.Integer, default=1)
    last_bounce_at = db.Column(db.DateTime)
    
    def __repr__(self):
        return f'<Suppression {self.email} - {self.type}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'email': self.email,
            'type': self.type,
            'reason': self.reason,
            'added_at': self.added_at.isoformat() if self.added_at else None,
            'bounce_count': self.bounce_count
        }
