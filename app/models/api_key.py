from app import db
from datetime import datetime
import uuid
import secrets
import hashlib

class APIKey(db.Model):
    __tablename__ = 'api_keys'
    
    id = db.Column(db.String(36), primary_key=True)
    organization_id = db.Column(db.String(36), db.ForeignKey('organizations.id'), nullable=False, index=True)
    
    name = db.Column(db.String(200), nullable=False)
    key_prefix = db.Column(db.String(20), nullable=False, unique=True, index=True)
    key_hash = db.Column(db.String(128), nullable=False)
    
    scopes = db.Column(db.JSON, default=list)
    
    rate_limit_per_minute = db.Column(db.Integer, default=100)
    rate_limit_per_hour = db.Column(db.Integer, default=1000)
    rate_limit_per_day = db.Column(db.Integer, default=10000)
    
    last_used_at = db.Column(db.DateTime)
    last_used_ip = db.Column(db.String(50))
    usage_count = db.Column(db.Integer, default=0)
    
    is_active = db.Column(db.Boolean, default=True, index=True)
    expires_at = db.Column(db.DateTime, nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    organization = db.relationship('Organization', backref='api_keys')
    
    def __init__(self, organization_id, name, scopes=None):
        self.id = str(uuid.uuid4())
        self.organization_id = organization_id
        self.name = name
        self.scopes = scopes or ['emails.send', 'emails.read']
        
        random_part = secrets.token_urlsafe(32)
        full_key = f"sb_live_{random_part}"
        
        self.key_prefix = f"sb_live_{random_part[:8]}"
        self.key_hash = hashlib.sha256(full_key.encode()).hexdigest()
        self._plain_key = full_key
    
    def verify_key(self, key: str) -> bool:
        key_hash = hashlib.sha256(key.encode()).hexdigest()
        return key_hash == self.key_hash
    
    def has_scope(self, scope: str) -> bool:
        return scope in (self.scopes or []) or '*' in (self.scopes or [])
    
    def to_dict(self, include_key=False):
        data = {
            'id': self.id,
            'name': self.name,
            'key_prefix': self.key_prefix,
            'scopes': self.scopes or [],
            'rate_limits': {
                'per_minute': self.rate_limit_per_minute,
                'per_hour': self.rate_limit_per_hour,
                'per_day': self.rate_limit_per_day
            },
            'is_active': self.is_active,
            'last_used_at': self.last_used_at.isoformat() if self.last_used_at else None,
            'usage_count': self.usage_count,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
        
        if include_key and hasattr(self, '_plain_key'):
            data['key'] = self._plain_key
        
        return data


class SMTPCredential(db.Model):
    __tablename__ = 'smtp_credentials'
    
    id = db.Column(db.String(36), primary_key=True)
    organization_id = db.Column(db.String(36), db.ForeignKey('organizations.id'), nullable=False, index=True)
    
    username = db.Column(db.String(100), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(128), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    allowed_from_domains = db.Column(db.JSON, default=list)
    
    rate_limit_per_minute = db.Column(db.Integer, default=60)
    rate_limit_per_hour = db.Column(db.Integer, default=500)
    
    last_used_at = db.Column(db.DateTime)
    emails_sent = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True, index=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    organization = db.relationship('Organization', backref='smtp_credentials')
    
    def __init__(self, organization_id, name):
        self.id = str(uuid.uuid4())
        self.organization_id = organization_id
        self.name = name
        
        org_prefix = str(organization_id)[:8]
        random_suffix = secrets.token_hex(4)
        self.username = f"smtp_{org_prefix}_{random_suffix}"
        
        plain_password = secrets.token_urlsafe(24)
        self.password_hash = hashlib.sha256(plain_password.encode()).hexdigest()
        self._plain_password = plain_password
    
    def verify_password(self, password: str) -> bool:
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        return password_hash == self.password_hash
    
    def to_dict(self, include_password=False):
        data = {
            'id': self.id,
            'name': self.name,
            'username': self.username,
            'smtp_host': 'smtp.sendbaba.com',
            'smtp_port': 587,
            'smtp_encryption': 'TLS',
            'allowed_from_domains': self.allowed_from_domains or [],
            'rate_limits': {
                'per_minute': self.rate_limit_per_minute,
                'per_hour': self.rate_limit_per_hour
            },
            'is_active': self.is_active,
            'last_used_at': self.last_used_at.isoformat() if self.last_used_at else None,
            'emails_sent': self.emails_sent,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
        
        if include_password and hasattr(self, '_plain_password'):
            data['password'] = self._plain_password
        
        return data


class APIRateLimit(db.Model):
    __tablename__ = 'api_rate_limits'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    api_key_id = db.Column(db.String(36), db.ForeignKey('api_keys.id', ondelete='CASCADE'))
    window_start = db.Column(db.DateTime, nullable=False, index=True)
    window_type = db.Column(db.String(20), nullable=False)  # 'minute', 'hour', 'day'
    request_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
