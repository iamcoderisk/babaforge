from app import db
from datetime import datetime

class Domain(db.Model):
    __tablename__ = 'domains'
    
    id = db.Column(db.String(36), primary_key=True)
    organization_id = db.Column(db.String(36), db.ForeignKey('organizations.id'), nullable=False)
    domain_name = db.Column(db.String(255), nullable=False, unique=True)
    dns_verified = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    dkim_selector = db.Column(db.String(100))
    dkim_private_key = db.Column(db.Text)
    dkim_public_key = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
