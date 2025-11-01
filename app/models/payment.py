from app import db
from datetime import datetime
import uuid

class PaymentMethod(db.Model):
    __tablename__ = 'payment_methods'
    
    id = db.Column(db.String(36), primary_key=True)
    organization_id = db.Column(db.String(36), db.ForeignKey('organizations.id'), nullable=False)
    
    # Card details (tokenized)
    authorization_code = db.Column(db.String(255))  # Korapay authorization code
    card_type = db.Column(db.String(50))  # visa, mastercard, etc
    last4 = db.Column(db.String(4))
    exp_month = db.Column(db.String(2))
    exp_year = db.Column(db.String(4))
    bank = db.Column(db.String(100))
    
    # Status
    is_default = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __init__(self, organization_id):
        self.id = str(uuid.uuid4())
        self.organization_id = organization_id
    
    def to_dict(self):
        return {
            'id': self.id,
            'card_type': self.card_type,
            'last4': self.last4,
            'exp_month': self.exp_month,
            'exp_year': self.exp_year,
            'bank': self.bank,
            'is_default': self.is_default,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class Transaction(db.Model):
    __tablename__ = 'transactions'
    
    id = db.Column(db.String(36), primary_key=True)
    organization_id = db.Column(db.String(36), db.ForeignKey('organizations.id'), nullable=False)
    subscription_id = db.Column(db.String(36), db.ForeignKey('subscriptions.id'))
    
    # Payment details
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    currency = db.Column(db.String(3), default='USD')
    
    # Korapay reference
    reference = db.Column(db.String(255), unique=True)
    korapay_reference = db.Column(db.String(255))
    
    # Status
    status = db.Column(db.String(20), default='pending')  # pending, success, failed
    payment_method = db.Column(db.String(50))  # card, bank_transfer
    
    # Response data
    response_data = db.Column(db.JSON)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    paid_at = db.Column(db.DateTime)
    
    def __init__(self, organization_id, amount, currency='USD'):
        self.id = str(uuid.uuid4())
        self.organization_id = organization_id
        self.amount = amount
        self.currency = currency
        self.reference = f"TXN-{uuid.uuid4().hex[:12].upper()}"
    
    def to_dict(self):
        return {
            'id': self.id,
            'reference': self.reference,
            'amount': float(self.amount),
            'currency': self.currency,
            'status': self.status,
            'payment_method': self.payment_method,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'paid_at': self.paid_at.isoformat() if self.paid_at else None
        }
