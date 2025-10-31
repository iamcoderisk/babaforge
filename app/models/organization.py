from app import db
from datetime import datetime
import uuid
import secrets

class Organization(db.Model):
    __tablename__ = 'organizations'
    
    id = db.Column(db.String(36), primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    slug = db.Column(db.String(100), unique=True, index=True)
    
    api_key = db.Column(db.String(64), unique=True, nullable=False, index=True)
    api_secret = db.Column(db.String(64), unique=True, nullable=False)
    
    timezone = db.Column(db.String(50), default='UTC')
    default_from_email = db.Column(db.String(255))
    default_from_name = db.Column(db.String(200))
    webhook_url = db.Column(db.String(500))
    webhook_secret = db.Column(db.String(64))
    
    is_active = db.Column(db.Boolean, default=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    domains = db.relationship('Domain', backref='organization', lazy=True, cascade='all, delete-orphan')
    
    def __init__(self, name, slug=None):
        self.id = str(uuid.uuid4())
        self.name = name
        self.slug = slug or name.lower().replace(' ', '-').replace('_', '-')[:50] + '-' + secrets.token_hex(4)
        self.api_key = secrets.token_urlsafe(32)
        self.api_secret = secrets.token_urlsafe(32)
        self.webhook_secret = secrets.token_urlsafe(16)
    
    def regenerate_api_key(self):
        self.api_key = secrets.token_urlsafe(32)
        self.api_secret = secrets.token_urlsafe(32)
