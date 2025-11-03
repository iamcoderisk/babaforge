from app import db
from datetime import datetime
import secrets
import uuid

class Domain(db.Model):
    __tablename__ = 'domains'
    
    id = db.Column(db.String(36), primary_key=True)
    organization_id = db.Column(db.String(36), db.ForeignKey('organizations.id'), nullable=False)
    domain_name = db.Column(db.String(255), unique=True, nullable=False, index=True)
    
    dns_verified = db.Column(db.Boolean, default=False)
    verification_token = db.Column(db.String(64), unique=True)
    
    dkim_selector = db.Column(db.String(64), default='default')
    dkim_private_key = db.Column(db.Text)
    dkim_public_key = db.Column(db.Text)
    
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    verified_at = db.Column(db.DateTime)
    
    def __init__(self, organization_id, domain_name):
        self.id = str(uuid.uuid4())
        self.organization_id = organization_id
        self.domain_name = domain_name.lower()
        self.verification_token = secrets.token_hex(16)
        self.generate_dkim_keys()
    
    def generate_dkim_keys(self):
        from cryptography.hazmat.primitives.asymmetric import rsa
        from cryptography.hazmat.primitives import serialization
        from cryptography.hazmat.backends import default_backend
        
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
            backend=default_backend()
        )
        
        self.dkim_private_key = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        ).decode('utf-8')
        
        public_key = private_key.public_key()
        public_pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        ).decode('utf-8')
        
        public_key_dns = public_pem.replace('-----BEGIN PUBLIC KEY-----', '')
        public_key_dns = public_key_dns.replace('-----END PUBLIC KEY-----', '')
        public_key_dns = public_key_dns.replace('\n', '')
        
        self.dkim_public_key = f"v=DKIM1; k=rsa; p={public_key_dns}"
    
    def get_dns_records(self):
        return {
            'spf': {
                'type': 'TXT',
                'name': '@',
                'value': f'v=spf1 ip4:156.67.29.186 include:sendbaba.com ~all',
                'ttl': 3600,
                'description': 'SPF record for email authentication'
            },
            'dkim': {
                'type': 'TXT',
                'name': f'{self.dkim_selector}._domainkey',
                'value': self.dkim_public_key,
                'ttl': 3600,
                'description': 'DKIM public key for email signing'
            },
            'dmarc': {
                'type': 'TXT',
                'name': '_dmarc',
                'value': 'v=DMARC1; p=none; rua=mailto:dmarc@sendbaba.com',
                'ttl': 3600,
                'description': 'DMARC policy for email authentication'
            },
            'verification': {
                'type': 'TXT',
                'name': f'_sendbaba-verify',
                'value': self.verification_token,
                'ttl': 3600,
                'description': 'Domain ownership verification'
            }
        }

class EmailUsage(db.Model):
    __tablename__ = 'email_usage'
    
    id = db.Column(db.String(36), primary_key=True)
    organization_id = db.Column(db.String(36), db.ForeignKey('organizations.id'), nullable=False)
    date = db.Column(db.Date, nullable=False, index=True)
    emails_sent = db.Column(db.Integer, default=0)
    emails_failed = db.Column(db.Integer, default=0)
    
    def __init__(self, organization_id, date):
        self.id = str(uuid.uuid4())
        self.organization_id = organization_id
        self.date = date

    def to_dict(self):
        """Convert domain to dictionary"""
        return {
            'id': self.id,
            'domain_name': self.domain_name,
            'dns_verified': self.dns_verified,
            'dkim_public_key': self.dkim_public_key,
            'verified_at': self.verified_at.isoformat() if self.verified_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

