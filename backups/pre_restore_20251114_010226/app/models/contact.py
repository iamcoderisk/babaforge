from app import db
from datetime import datetime
import uuid

class Contact(db.Model):
    __tablename__ = 'contacts'
    
    id = db.Column(db.String(36), primary_key=True)
    organization_id = db.Column(db.String(36), db.ForeignKey('organizations.id'), nullable=False, index=True)
    
    # Contact info
    email = db.Column(db.String(255), nullable=False, index=True)
    first_name = db.Column(db.String(100))
    last_name = db.Column(db.String(100))
    phone = db.Column(db.String(50))
    company = db.Column(db.String(200))
    
    # Custom fields (JSON)
    custom_fields = db.Column(db.JSON)
    
    # Status
    status = db.Column(db.String(20), default='active', index=True)  # active, unsubscribed, bounced, complained
    
    # Lists and tags
    lists = db.Column(db.JSON, default=list)  # Array of list IDs
    tags = db.Column(db.JSON, default=list)  # Array of tags
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Constraints
    __table_args__ = (
        db.UniqueConstraint('organization_id', 'email', name='unique_contact_per_org'),
    )
    
    def __init__(self, organization_id, email, **kwargs):
        self.id = str(uuid.uuid4())
        self.organization_id = organization_id
        self.email = email.lower().strip()
        
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    @property
    def full_name(self):
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        elif self.first_name:
            return self.first_name
        elif self.last_name:
            return self.last_name
        return self.email
    
    def to_dict(self):
        return {
            'id': self.id,
            'email': self.email,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'phone': self.phone,
            'company': self.company,
            'custom_fields': self.custom_fields,
            'status': self.status,
            'lists': self.lists or [],
            'tags': self.tags or [],
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class ContactList(db.Model):
    __tablename__ = 'contact_lists'
    
    id = db.Column(db.String(36), primary_key=True)
    organization_id = db.Column(db.String(36), db.ForeignKey('organizations.id'), nullable=False, index=True)
    
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    contact_count = db.Column(db.Integer, default=0)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __init__(self, organization_id, name, description=None):
        self.id = str(uuid.uuid4())
        self.organization_id = organization_id
        self.name = name
        self.description = description
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'contact_count': self.contact_count,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class BulkImport(db.Model):
    __tablename__ = 'bulk_imports'
    
    id = db.Column(db.String(36), primary_key=True)
    organization_id = db.Column(db.String(36), db.ForeignKey('organizations.id'), nullable=False, index=True)
    
    filename = db.Column(db.String(255))
    status = db.Column(db.String(20), default='processing', index=True)  # processing, completed, failed
    
    # Stats
    total_rows = db.Column(db.Integer, default=0)
    processed_rows = db.Column(db.Integer, default=0)
    successful_imports = db.Column(db.Integer, default=0)
    failed_imports = db.Column(db.Integer, default=0)
    duplicate_emails = db.Column(db.Integer, default=0)
    
    # Error log
    errors = db.Column(db.JSON, default=list)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)
    
    def __init__(self, organization_id, filename=None):
        self.id = str(uuid.uuid4())
        self.organization_id = organization_id
        self.filename = filename
    
    def to_dict(self):
        return {
            'id': self.id,
            'filename': self.filename,
            'status': self.status,
            'total_rows': self.total_rows,
            'processed_rows': self.processed_rows,
            'successful_imports': self.successful_imports,
            'failed_imports': self.failed_imports,
            'duplicate_emails': self.duplicate_emails,
            'errors': self.errors or [],
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None
        }
