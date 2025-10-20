import asyncio
import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import dkim
import gzip

from app.models.database import EmailOutgoing, Organization, Domain
from app.models.schemas import EmailSendRequest
from app.services.dkim_service import DKIMService
from app.services.queue_service import QueueService
from app.config.settings import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)

class EmailService:
    """Email sending and processing service"""
    
    def __init__(self, db: Session):
        self.db = db
        self.dkim_service = DKIMService()
        self.queue_service = QueueService()
    
    async def send_email(
        self, 
        org_id: int, 
        email_request: EmailSendRequest
    ) -> EmailOutgoing:
        """Send single email"""
        
        # Get organization
        org = self.db.query(Organization).filter_by(id=org_id).first()
        if not org:
            raise ValueError(f"Organization {org_id} not found")
        
        # Check rate limits
        await self._check_rate_limits(org)
        
        # Create email record
        email = EmailOutgoing(
            org_id=org_id,
            message_id=str(uuid.uuid4()),
            sender=email_request.from_email or f"noreply@{settings.PRIMARY_DOMAIN}",
            recipients=email_request.to,
            subject=email_request.subject,
            body_text=email_request.body_text,
            body_html=email_request.body_html,
            headers=email_request.headers or {},
            tags=email_request.tags or [],
            metadata_=email_request.metadata or {},
            priority=email_request.priority,
            status='queued',
            created_at=datetime.utcnow()
        )
        
        self.db.add(email)
        self.db.commit()
        self.db.refresh(email)
        
        # Queue for sending
        await self.queue_service.enqueue_email(email)
        
        logger.info(f"Email queued: {email.message_id}")
        return email
    
    async def send_batch(
        self,
        org_id: int,
        email_requests: List[EmailSendRequest]
    ) -> List[EmailOutgoing]:
        """Send batch of emails"""
        
        emails = []
        for request in email_requests:
            email = await self.send_email(org_id, request)
            emails.append(email)
        
        logger.info(f"Batch of {len(emails)} emails queued")
        return emails
    
    async def process_outgoing_email(self, email: EmailOutgoing):
        """Process and send outgoing email"""
        
        try:
            # Get organization
            org = self.db.query(Organization).filter_by(id=email.org_id).first()
            
            # Get domain
            sender_domain = email.sender.split('@')[1]
            domain = self.db.query(Domain).filter_by(
                org_id=org.id,
                domain=sender_domain
            ).first()
            
            # Create MIME message
            message = await self._create_mime_message(email)
            
            # Sign with DKIM
            if domain and domain.dkim_public_key:
                signed_message = self.dkim_service.sign_message(
                    message.as_bytes(),
                    domain.domain,
                    domain.dkim_selector
                )
                email.dkim_signed = True
            else:
                signed_message = message.as_bytes()
            
            # Send via SMTP
            await self._send_via_smtp(email, signed_message)
            
            # Update status
            email.status = 'sent'
            email.delivered_at = datetime.utcnow()
            
        except Exception as e:
            logger.error(f"Error sending email {email.message_id}: {e}")
            email.status = 'failed'
            email.bounce_reason = str(e)
            email.attempt_count += 1
            
            # Retry logic
            if email.attempt_count < email.max_attempts:
                email.status = 'retry'
                email.next_retry_at = self._calculate_retry_time(email.attempt_count)
        
        self.db.commit()
    
    async def _send_via_smtp(self, email: EmailOutgoing, message: bytes):
        """Send email via SMTP"""
        
        # Get sending IP from pool
        sending_ip = await self._get_sending_ip(email.org_id)
        email.sending_ip = sending_ip
        
        # Connect and send
        for recipient in email.recipients:
            try:
                # Extract domain
                recipient_domain = recipient.split('@')[1]
                
                # Get MX records
                mx_records = await self._get_mx_records(recipient_domain)
                
                # Try each MX in order
                for mx in mx_records:
                    try:
                        async with aiosmtplib.SMTP(
                            hostname=mx,
                            port=settings.SMTP_PORT,
                            timeout=settings.CONNECTION_TIMEOUT,
                            source_address=(sending_ip, 0) if sending_ip else None
                        ) as smtp:
                            await smtp.send_message(message)
                            logger.info(f"Email sent to {recipient} via {mx}")
                            break
                    except Exception as e:
                        logger.warning(f"Failed to send via {mx}: {e}")
                        continue
                else:
                    raise Exception(f"Failed to deliver to {recipient}")
                    
            except Exception as e:
                logger.error(f"Error sending to {recipient}: {e}")
                raise
    
    async def _create_mime_message(self, email: EmailOutgoing) -> MIMEMultipart:
        """Create MIME message from email"""
        
        msg = MIMEMultipart('alternative')
        msg['From'] = email.sender
        msg['To'] = ', '.join(email.recipients[:10])  # Limit header size
        msg['Subject'] = email.subject
        msg['Message-ID'] = f"<{email.message_id}@{settings.PRIMARY_DOMAIN}>"
        msg['Date'] = email.created_at.strftime('%a, %d %b %Y %H:%M:%S +0000')
        
        # Add custom headers
        for key, value in email.headers.items():
            msg[key] = value
        
        # Add tracking pixel if enabled
        if settings.ENABLE_EMAIL_TRACKING:
            tracking_pixel = f'<img src="https://{settings.HOSTNAME}/track/open/{email.message_id}" width="1" height="1" />'
            if email.body_html:
                email.body_html += tracking_pixel
        
        # Add body parts
        if email.body_text:
            msg.attach(MIMEText(email.body_text, 'plain', 'utf-8'))
        
        if email.body_html:
            msg.attach(MIMEText(email.body_html, 'html', 'utf-8'))
        
        return msg
    
    async def _get_sending_ip(self, org_id: int) -> Optional[str]:
        """Get next IP from pool for organization"""
        # Implementation for IP rotation
        return None
    
    async def _get_mx_records(self, domain: str) -> List[str]:
        """Get MX records for domain"""
        import dns.resolver
        try:
            mx_records = dns.resolver.resolve(domain, 'MX')
            return [str(mx.exchange).rstrip('.') for mx in sorted(mx_records, key=lambda x: x.preference)]
        except Exception as e:
            logger.error(f"Error getting MX for {domain}: {e}")
            return [domain]
    
    async def _check_rate_limits(self, org: Organization):
        """Check rate limits for organization"""
        from app.services.rate_limiter import RateLimiter
        rate_limiter = RateLimiter()
        
        allowed = await rate_limiter.check_limit(
            org.id,
            max_per_second=org.max_emails_per_second,
            max_per_minute=org.max_emails_per_minute,
            max_per_hour=org.max_emails_per_hour
        )
        
        if not allowed:
            raise Exception("Rate limit exceeded")
    
    def _calculate_retry_time(self, attempt: int) -> datetime:
        """Calculate exponential backoff retry time"""
        from datetime import timedelta
        delay_minutes = 2 ** attempt
        return datetime.utcnow() + timedelta(minutes=delay_minutes)
