from app import db
from datetime import datetime

class ContactList(db.Model):
    __tablename__ = 'contact_lists'
    __table_args__ = {'extend_existing': True}
    
    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.Integer, db.ForeignKey('organizations.id'), nullable=False)
    
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    
    # Stats
    total_contacts = db.Column(db.Integer, default=0)
    active_contacts = db.Column(db.Integer, default=0)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    organization = db.relationship('Organization', backref='contact_lists')
    
    def __repr__(self):
        return f'<ContactList {self.id}: {self.name}>'
