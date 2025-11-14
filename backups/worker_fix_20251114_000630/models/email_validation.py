from app import db
from datetime import datetime

class EmailValidation(db.Model):
    __tablename__ = 'email_validations'
    
    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.Integer, db.ForeignKey('organizations.id'))
    email = db.Column(db.String(255), nullable=False)
    status = db.Column(db.String(50))  # valid, invalid, risky, unknown
    score = db.Column(db.Integer)
    checks = db.Column(db.JSON)
    validated_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    organization = db.relationship('Organization')
