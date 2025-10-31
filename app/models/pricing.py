from app import db
from datetime import datetime
import uuid

class PricingPlan(db.Model):
    __tablename__ = 'pricing_plans'
    
    id = db.Column(db.String(36), primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    slug = db.Column(db.String(50), unique=True, nullable=False)
    
    # Pricing
    price = db.Column(db.Numeric(10, 2), nullable=False)
    currency = db.Column(db.String(3), default='USD')
    
    # Email limits
    emails_included = db.Column(db.Integer, nullable=False)
    
    # Features
    features = db.Column(db.JSON)  # List of features
    
    # Advanced features flags
    has_advanced_analytics = db.Column(db.Boolean, default=False)
    has_click_tracking = db.Column(db.Boolean, default=False)
    has_open_tracking = db.Column(db.Boolean, default=False)
    has_webhooks = db.Column(db.Boolean, default=False)
    has_suppression_lists = db.Column(db.Boolean, default=False)
    has_bounce_handling = db.Column(db.Boolean, default=False)
    
    # Limits
    max_sending_domains = db.Column(db.Integer, default=1)
    max_api_calls_per_minute = db.Column(db.Integer, default=60)
    
    # Display
    is_active = db.Column(db.Boolean, default=True)
    display_order = db.Column(db.Integer, default=0)
    is_popular = db.Column(db.Boolean, default=False)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __init__(self, name, slug, price, emails_included):
        self.id = str(uuid.uuid4())
        self.name = name
        self.slug = slug
        self.price = price
        self.emails_included = emails_included
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'slug': self.slug,
            'price': float(self.price),
            'currency': self.currency,
            'emails_included': self.emails_included,
            'features': self.features or [],
            'has_advanced_analytics': self.has_advanced_analytics,
            'max_sending_domains': self.max_sending_domains,
            'is_popular': self.is_popular
        }

class Subscription(db.Model):
    __tablename__ = 'subscriptions'
    
    id = db.Column(db.String(36), primary_key=True)
    organization_id = db.Column(db.String(36), db.ForeignKey('organizations.id'), nullable=False)
    plan_id = db.Column(db.String(36), db.ForeignKey('pricing_plans.id'), nullable=False)
    
    # Status
    status = db.Column(db.String(20), default='active')  # active, cancelled, expired, suspended
    
    # Usage
    emails_sent_this_period = db.Column(db.Integer, default=0)
    period_start = db.Column(db.DateTime, default=datetime.utcnow)
    period_end = db.Column(db.DateTime)
    
    # Add-ons
    extra_dedicated_ips = db.Column(db.Integer, default=0)
    
    # Billing
    next_billing_date = db.Column(db.DateTime)
    last_payment_date = db.Column(db.DateTime)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    plan = db.relationship('PricingPlan', backref='subscriptions')
    
    def __init__(self, organization_id, plan_id):
        self.id = str(uuid.uuid4())
        self.organization_id = organization_id
        self.plan_id = plan_id
    
    def to_dict(self):
        return {
            'id': self.id,
            'plan': self.plan.to_dict() if self.plan else None,
            'status': self.status,
            'emails_sent': self.emails_sent_this_period,
            'emails_remaining': self.plan.emails_included - self.emails_sent_this_period if self.plan else 0,
            'period_start': self.period_start.isoformat() if self.period_start else None,
            'period_end': self.period_end.isoformat() if self.period_end else None,
            'extra_dedicated_ips': self.extra_dedicated_ips
        }

class EmailTracking(db.Model):
    __tablename__ = 'email_tracking'
    
    id = db.Column(db.String(36), primary_key=True)
    email_id = db.Column(db.String(36), db.ForeignKey('emails.id'), nullable=False)
    
    # Tracking data
    opened = db.Column(db.Boolean, default=False)
    opened_at = db.Column(db.DateTime)
    open_count = db.Column(db.Integer, default=0)
    
    clicked = db.Column(db.Boolean, default=False)
    clicked_at = db.Column(db.DateTime)
    click_count = db.Column(db.Integer, default=0)
    clicked_links = db.Column(db.JSON)  # List of clicked URLs
    
    # Device/Location data
    user_agent = db.Column(db.Text)
    ip_address = db.Column(db.String(45))
    country = db.Column(db.String(2))
    city = db.Column(db.String(100))
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __init__(self, email_id):
        self.id = str(uuid.uuid4())
        self.email_id = email_id
