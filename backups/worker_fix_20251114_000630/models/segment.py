from app import db
from datetime import datetime

class Segment(db.Model):
    __tablename__ = 'segments'
    
    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.Integer, db.ForeignKey('organizations.id'))
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    conditions = db.Column(db.JSON)  # array of conditions
    is_dynamic = db.Column(db.Boolean, default=True)
    contacts_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    organization = db.relationship('Organization', backref='segments')
