from app import db
from datetime import datetime

class IPWarmup(db.Model):
    __tablename__ = 'ip_warmups'
    
    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.Integer, db.ForeignKey('organizations.id'))
    ip_address = db.Column(db.String(50))
    start_date = db.Column(db.Date, default=datetime.utcnow().date)
    current_day = db.Column(db.Integer, default=1)
    status = db.Column(db.String(20), default='active')  # active, paused, completed
    completed_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    organization = db.relationship('Organization', backref='ip_warmups')
