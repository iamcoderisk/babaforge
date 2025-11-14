import asyncio
from typing import List, Dict
from collections import defaultdict

from app.models.database import EmailOutgoing
from app.services.smtp_pool import smtp_pool
from app.utils.logger import get_logger

logger = get_logger(__name__)

class BatchProcessor:
    """Process emails in optimized batches"""
    
    def __init__(self, batch_size: int = 5000):
        self.batch_size = batch_size
    
    def group_by_domain(self, emails: List[EmailOutgoing]) -> Dict[str, List[EmailOutgoing]]:
        """Group emails by recipient domain"""
        grouped = defaultdict(list)
        
        for email in emails:
            for recipient in email.recipients:
                domain = recipient.split('@')[1]
                grouped[domain].append(email)
        
        return grouped
    
    async def process_batch(self, emails: List[EmailOutgoing]):
        """Process batch of emails efficiently"""
        
        # Group by domain
        by_domain = self.group_by_domain(emails)
        
        logger.info(f"Processing {len(emails)} emails across {len(by_domain)} domains")
        
        # Process each domain concurrently
        tasks = []
        for domain, domain_emails in by_domain.items():
            task = self.process_domain_batch(domain, domain_emails)
            tasks.append(task)
        
        # Wait for all domains
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Count successes/failures
        success_count = sum(1 for r in results if r and not isinstance(r, Exception))
        failure_count = len(results) - success_count
        
        logger.info(f"Batch complete: {success_count} success, {failure_count} failed")
        
        return {
            'success': success_count,
            'failed': failure_count,
            'total': len(emails)
        }
    
    async def process_domain_batch(self, domain: str, emails: List[EmailOutgoing]):
        """Process all emails for a single domain"""
        
        try:
            # Get MX record
            mx_host = await self.get_mx_host(domain)
            
            # Send all emails through same connection
            for email in emails:
                message = await self.create_message(email)
                success = await smtp_pool.send_message(message, mx_host)
                
                if success:
                    email.status = 'sent'
                else:
                    email.status = 'failed'
            
            return True
            
        except Exception as e:
            logger.error(f"Error processing domain {domain}: {e}")
            for email in emails:
                email.status = 'failed'
                email.bounce_reason = str(e)
            return False
    
    async def get_mx_host(self, domain: str) -> str:
        """Get MX host for domain"""
        import dns.resolver
        try:
            mx_records = dns.resolver.resolve(domain, 'MX')
            return str(sorted(mx_records, key=lambda x: x.preference)[0].exchange).rstrip('.')
        except:
            return domain
    
    async def create_message(self, email: EmailOutgoing) -> bytes:
        """Create MIME message"""
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart
        
        msg = MIMEMultipart()
        msg['From'] = email.sender
        msg['To'] = ', '.join(email.recipients)
        msg['Subject'] = email.subject
        msg['Message-ID'] = f"<{email.message_id}@{settings.PRIMARY_DOMAIN}>"
        
        if email.body_text:
            msg.attach(MIMEText(email.body_text, 'plain'))
        
        if email.body_html:
            msg.attach(MIMEText(email.body_html, 'html'))
        
        return msg.as_bytes()
