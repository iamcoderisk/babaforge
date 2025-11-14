from app import db
from datetime import datetime

class EmailTemplate(db.Model):
    __tablename__ = 'email_templates'
    
    id = db.Column(db.String(36), primary_key=True)
    organization_id = db.Column(db.String(36), db.ForeignKey('organizations.id'), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    subject = db.Column(db.String(500))
    html_content = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'subject': self.subject,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
