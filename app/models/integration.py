from app import db
from datetime import datetime

class Integration(db.Model):
    __tablename__ = 'integrations'
    
    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.Integer, db.ForeignKey('organizations.id'))
    
    platform = db.Column(db.String(50))  # shopify, woocommerce, magento
    name = db.Column(db.String(255))
    config = db.Column(db.JSON)  # Store credentials
    is_active = db.Column(db.Boolean, default=True)
    last_sync = db.Column(db.DateTime)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    organization = db.relationship('Organization', backref='integrations')
