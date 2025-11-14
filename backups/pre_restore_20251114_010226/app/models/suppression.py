from app import db
from datetime import datetime

class SuppressionList(db.Model):
    __tablename__ = 'suppression_list'
    
    id = db.Column(db.String(36), primary_key=True)
    organization_id = db.Column(db.String(36), db.ForeignKey('organizations.id'))
    email = db.Column(db.String(255), nullable=False, unique=True)
    reason = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
