import email
import re
from email.parser import BytesParser
from aiosmtpd.controller import Controller
from aiosmtpd.smtp import SMTP as SMTPServer
from app import create_app, db
from app.models.reply import EmailReply
from app.models.contact import Contact
from app.services.reply_intelligence import reply_intelligence
from app.services.email_service import send_email
import logging

logger = logging.getLogger(__name__)

class ReplyHandler:
    """Handle incoming email replies"""
    
    def __init__(self):
        self.app = create_app()
    
    async def handle_DATA(self, server, session, envelope):
        """Process incoming email"""
        try:
            with self.app.app_context():
                # Parse email
                parser = BytesParser()
                message = parser.parsebytes(envelope.content)
                
                # Extract recipient address
                to_address = envelope.rcpt_tos[0] if envelope.rcpt_tos else None
                
                if not to_address:
                    return '250 Message accepted'
                
                # Parse reply tracking from address
                # Format: reply-{campaign_id}-{contact_id}@mail.sendbaba.com
                tracking_info = self.parse_tracking_address(to_address)
                
                if not tracking_info:
                    logger.warning(f"Could not parse tracking from: {to_address}")
                    return '250 Message accepted'
                
                # Extract email content
                text_body = self.get_text_body(message)
                html_body = self.get_html_body(message)
                subject = message.get('subject', '')
                from_email = message.get('from', '')
                from_name = self.extract_name_from_email(from_email)
                message_id = message.get('message-id', '')
                in_reply_to = message.get('in-reply-to', '')
                
                # Clean reply text (remove quoted text)
                clean_text = self.clean_reply_text(text_body)
                
                # Analyze with AI
                analysis = reply_intelligence.analyze_reply(clean_text, subject)
                
                # Find or create contact
                contact = Contact.query.filter_by(
                    email=self.extract_email(from_email)
                ).first()
                
                contact_id = contact.id if contact else None
                
                # Save reply to database
                reply = EmailReply(
                    organization_id=tracking_info['organization_id'],
                    campaign_id=tracking_info.get('campaign_id'),
                    contact_id=contact_id,
                    from_email=self.extract_email(from_email),
                    from_name=from_name,
                    subject=subject,
                    text_body=clean_text,
                    html_body=html_body,
                    message_id=message_id,
                    in_reply_to=in_reply_to,
                    sentiment=analysis['sentiment'],
                    sentiment_score=analysis['sentiment_score'],
                    intent=analysis['intent'],
                    category=analysis['category'],
                    urgency=analysis['urgency'],
                    raw_email=envelope.content.decode('utf-8', errors='ignore')
                )
                
                db.session.add(reply)
                db.session.commit()
                
                logger.info(f"Reply captured: {reply.id} from {from_email}")
                
                # Check if we should auto-respond
                should_respond, template_id = reply_intelligence.should_auto_respond(
                    analysis['category'],
                    analysis['intent'],
                    tracking_info['organization_id']
                )
                
                if should_respond:
                    self.send_auto_response(reply, template_id)
                
                # Send notification to team
                self.notify_team(reply)
                
                return '250 Message accepted'
                
        except Exception as e:
            logger.error(f"Error processing reply: {e}", exc_info=True)
            return '250 Message accepted'  # Accept anyway to not bounce
    
    def parse_tracking_address(self, address):
        """Parse tracking info from reply-to address"""
        # Format: reply-campaign123-contact456@mail.sendbaba.com
        # Or: reply-org789@mail.sendbaba.com
        
        match = re.match(r'reply-(?:campaign)?(\d+)-(?:contact)?(\d+)@', address)
        if match:
            return {
                'campaign_id': int(match.group(1)),
                'contact_id': int(match.group(2)),
                'organization_id': self.get_org_from_campaign(int(match.group(1)))
            }
        
        # Try simpler format
        match = re.match(r'reply-org(\d+)@', address)
        if match:
            return {
                'organization_id': int(match.group(1)),
                'campaign_id': None,
                'contact_id': None
            }
        
        return None
    
    def get_org_from_campaign(self, campaign_id):
        """Get organization ID from campaign"""
        from app.models.campaign import Campaign
        campaign = Campaign.query.get(campaign_id)
        return campaign.organization_id if campaign else None
    
    def get_text_body(self, message):
        """Extract plain text from email"""
        if message.is_multipart():
            for part in message.walk():
                if part.get_content_type() == 'text/plain':
                    return part.get_payload(decode=True).decode('utf-8', errors='ignore')
        else:
            if message.get_content_type() == 'text/plain':
                return message.get_payload(decode=True).decode('utf-8', errors='ignore')
        return ''
    
    def get_html_body(self, message):
        """Extract HTML from email"""
        if message.is_multipart():
            for part in message.walk():
                if part.get_content_type() == 'text/html':
                    return part.get_payload(decode=True).decode('utf-8', errors='ignore')
        return ''
    
    def clean_reply_text(self, text):
        """Remove quoted text from reply"""
        if not text:
            return ''
        
        # Remove common reply markers
        lines = text.split('\n')
        clean_lines = []
        
        for line in lines:
            # Stop at common quote markers
            if any(marker in line for marker in ['On ', 'From:', '>', '-----Original Message-----']):
                break
            clean_lines.append(line)
        
        return '\n'.join(clean_lines).strip()
    
    def extract_email(self, from_field):
        """Extract email address from From field"""
        match = re.search(r'<(.+?)>', from_field)
        if match:
            return match.group(1)
        return from_field.strip()
    
    def extract_name_from_email(self, from_field):
        """Extract name from From field"""
        match = re.match(r'(.+?)\s*<', from_field)
        if match:
            return match.group(1).strip('"')
        return ''
    
    def send_auto_response(self, reply, template_id=None):
        """Send automatic response"""
        from app.models.reply import ReplyTemplate
        
        # Get template
        if template_id:
            template = ReplyTemplate.query.get(template_id)
        else:
            # Use default template for category
            template = ReplyTemplate.query.filter_by(
                organization_id=reply.organization_id,
                category=reply.category,
                is_active=True,
                auto_send=True
            ).first()
        
        if not template:
            logger.info(f"No template found for reply {reply.id}")
            return
        
        # Personalize template
        contact = reply.contact
        body = template.body
        
        if contact:
            body = body.replace('{{first_name}}', contact.first_name or 'there')
            body = body.replace('{{last_name}}', contact.last_name or '')
            body = body.replace('{{email}}', contact.email or '')
        
        # Send response
        try:
            send_email(
                to=reply.from_email,
                from_email='noreply@sendbaba.com',
                from_name='SendBaba',
                subject=f"Re: {reply.subject}" if reply.subject else template.subject,
                body=body,
                in_reply_to=reply.message_id
            )
            
            # Mark as auto-responded
            reply.auto_responded = True
            reply.responded = True
            reply.responded_at = datetime.utcnow()
            reply.response_text = body
            
            # Update template usage
            template.times_used += 1
            
            db.session.commit()
            
            logger.info(f"Auto-response sent for reply {reply.id}")
            
        except Exception as e:
            logger.error(f"Error sending auto-response: {e}")
    
    def notify_team(self, reply):
        """Notify team about new reply"""
        # TODO: Send notification email or Slack message
        pass

def start_reply_catcher(host='0.0.0.0', port=2525):
    """Start the reply catcher SMTP server"""
    handler = ReplyHandler()
    controller = Controller(handler, hostname=host, port=port)
    controller.start()
    logger.info(f"Reply catcher started on {host}:{port}")
    return controller
