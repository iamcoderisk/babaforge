from app import db
from datetime import datetime

class Form(db.Model):
    __tablename__ = 'forms'
    
    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.Integer, db.ForeignKey('organizations.id'))
    name = db.Column(db.String(255), nullable=False)
    form_type = db.Column(db.String(50))  # inline, popup, slide-in, sticky
    trigger_config = db.Column(db.JSON)  # exit-intent, scroll, time, etc.
    design_config = db.Column(db.JSON)  # colors, fonts, etc.
    fields = db.Column(db.JSON)  # form fields configuration
    success_message = db.Column(db.Text)
    redirect_url = db.Column(db.String(500))
    is_active = db.Column(db.Boolean, default=True)
    submissions = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    organization = db.relationship('Organization', backref='forms')

class FormSubmission(db.Model):
    __tablename__ = 'form_submissions'
    
    id = db.Column(db.Integer, primary_key=True)
    form_id = db.Column(db.Integer, db.ForeignKey('forms.id'))
    contact_id = db.Column(db.Integer, db.ForeignKey('contacts.id'))
    data = db.Column(db.JSON)
    ip_address = db.Column(db.String(50))
    user_agent = db.Column(db.String(500))
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    form = db.relationship('Form', backref='submissions_list')
    contact = db.relationship('Contact')
