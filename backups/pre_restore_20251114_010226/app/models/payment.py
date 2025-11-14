from app import db
from datetime import datetime

class PaymentMethod(db.Model):
    __tablename__ = 'payment_methods'
    
    id = db.Column(db.String(36), primary_key=True)
    organization_id = db.Column(db.String(36), db.ForeignKey('organizations.id'), nullable=False)
    authorization_code = db.Column(db.String(255))
    card_type = db.Column(db.String(50))
    last4 = db.Column(db.String(4))
    exp_month = db.Column(db.Integer)
    exp_year = db.Column(db.Integer)
    bank = db.Column(db.String(100))
    is_default = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Transaction(db.Model):
    __tablename__ = 'transactions'
    
    id = db.Column(db.String(36), primary_key=True)
    organization_id = db.Column(db.String(36), db.ForeignKey('organizations.id'), nullable=False)
    subscription_id = db.Column(db.String(36), db.ForeignKey('subscriptions.id'))
    reference = db.Column(db.String(100), unique=True)
    korapay_reference = db.Column(db.String(100))
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    currency = db.Column(db.String(3), default='USD')
    status = db.Column(db.String(20), default='pending')
    paid_at = db.Column(db.DateTime)
    response_data = db.Column(db.JSON)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
