from app.models.user import User
from app.models.organization import Organization
from app.models.email import Email, EmailTracking, EmailClick, EmailOpen, EmailBounce, EmailUnsubscribe
from app.models.contact import Contact, ContactList
from app.models.campaign import Campaign, CampaignRecipient, CampaignAnalytics
from app.models.template import EmailTemplate
from app.models.domain import Domain
from app.models.suppression import SuppressionList
from app.models.pricing import PricingPlan, Subscription
from app.models.payment import PaymentMethod, Transaction

# Import reply models if they exist, but don't fail if they don't
try:
    from app.models.reply import EmailReply
except ImportError:
    pass

__all__ = [
    'User',
    'Organization', 
    'Email',
    'EmailTracking',
    'EmailClick',
    'EmailOpen',
    'EmailBounce',
    'EmailUnsubscribe',
    'Contact',
    'ContactList',
    'Campaign',
    'CampaignRecipient',
    'CampaignAnalytics',
    'EmailTemplate',
    'Domain',
    'SuppressionList',
    'PricingPlan',
    'Subscription',
    'PaymentMethod',
    'Transaction',
]
