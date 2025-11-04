from app import db
from datetime import datetime

class EmailTemplate(db.Model):
    __tablename__ = 'email_templates'
    
    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.Integer, db.ForeignKey('organizations.id'))
    name = db.Column(db.String(255), nullable=False)
    category = db.Column(db.String(100))
    thumbnail = db.Column(db.String(500))
    html_content = db.Column(db.Text)
    json_structure = db.Column(db.JSON)
    is_public = db.Column(db.Boolean, default=False)
    is_system = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    organization = db.relationship('Organization', backref='email_templates')

class SavedBlock(db.Model):
    __tablename__ = 'saved_blocks'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    organization_id = db.Column(db.Integer, db.ForeignKey('organizations.id'))
    name = db.Column(db.String(255))
    html_content = db.Column(db.Text)
    json_structure = db.Column(db.JSON)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', backref='saved_blocks')
