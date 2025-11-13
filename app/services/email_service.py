import asyncio
import logging
from app.smtp.relay_server import send_via_relay

logger = logging.getLogger(__name__)

def generate_reply_address(campaign_id, contact_id, organization_id):
    """Generate unique reply-to address for tracking"""
    if campaign_id and contact_id:
        return f"reply-campaign{campaign_id}-contact{contact_id}@mail.sendbaba.com"
    elif organization_id:
        return f"reply-org{organization_id}@mail.sendbaba.com"
    else:
        return "noreply@sendbaba.com"

def send_email(to_email, subject, body, from_email=None, from_name=None, organization_id=None):
    """
    Send email using SendBaba's SMTP relay engine
    Sends directly to recipient's MX server
    """
    try:
        from_email = from_email or 'noreply@sendbaba.com'
        from_name = from_name or 'SendBaba'
        
        # Prepare email data for SendBaba's relay
        email_data = {
            'from': from_email,
            'to': to_email,
            'subject': subject,
            'html_body': body,
            'text_body': '',
            'id': f'sendbaba-{hash(to_email)}'
        }
        
        logger.info(f"📧 Sending email to {to_email} via SendBaba SMTP relay")
        
        # Send via SendBaba's relay (runs async)
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(send_via_relay(email_data))
        loop.close()
        
        if result.get('success'):
            logger.info(f"✅ Email sent to {to_email} via {result.get('mx_server')}")
            return True
        else:
            logger.error(f"❌ Failed to send to {to_email}: {result.get('message')}")
            return False
        
    except Exception as e:
        logger.error(f"❌ Email send error: {str(e)}")
        return False
