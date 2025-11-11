"""
Custom SMTP Relay Server
Sends emails directly to recipient MX servers
"""
import asyncio
import smtplib
import dns.resolver
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formataddr
import logging

logger = logging.getLogger(__name__)


async def send_via_relay(email_data: dict) -> dict:
    """
    Send email directly to recipient's MX server
    
    Args:
        email_data: Dict with 'from', 'to', 'subject', 'html_body', 'text_body'
    
    Returns:
        Dict with 'success', 'message', 'mx_server'
    """
    try:
        from_email = email_data.get('from', 'noreply@sendbaba.com')
        to_email = email_data.get('to')
        subject = email_data.get('subject', 'No Subject')
        html_body = email_data.get('html_body', '')
        text_body = email_data.get('text_body', '')
        
        if not to_email:
            return {'success': False, 'message': 'No recipient email'}
        
        # Get recipient domain
        recipient_domain = to_email.split('@')[1]
        
        # Lookup MX records
        try:
            mx_records = dns.resolver.resolve(recipient_domain, 'MX')
            mx_records = sorted(mx_records, key=lambda x: x.preference)
            mx_server = str(mx_records[0].exchange).rstrip('.')
            logger.info(f"Trying MX: {mx_server}")
        except Exception as e:
            logger.error(f"MX lookup failed for {recipient_domain}: {e}")
            return {
                'success': False,
                'message': f'MX lookup failed: {str(e)}',
                'bounce': True,
                'bounce_type': 'hard'
            }
        
        # Create email message
        msg = MIMEMultipart('alternative')
        msg['From'] = from_email
        msg['To'] = to_email
        msg['Subject'] = subject
        msg['Message-ID'] = f"<{email_data.get('id', 'unknown')}@sendbaba.com>"
        
        # Add plain text part
        if text_body:
            text_part = MIMEText(text_body, 'plain', 'utf-8')
            msg.attach(text_part)
        
        # Add HTML part
        if html_body:
            html_part = MIMEText(html_body, 'html', 'utf-8')
            msg.attach(html_part)
        elif not text_body:
            # If neither provided, create basic text
            default_body = email_data.get('body', 'This is a test email from SendBaba.')
            text_part = MIMEText(default_body, 'plain', 'utf-8')
            msg.attach(text_part)
        
        # Send email via SMTP
        try:
            with smtplib.SMTP(mx_server, 25, timeout=30) as smtp:
                smtp.ehlo('sendbaba.com')
                
                # Try STARTTLS if available
                try:
                    smtp.starttls()
                    smtp.ehlo('sendbaba.com')
                except:
                    pass
                
                smtp.send_message(msg)
                
            logger.info(f"✅ Email sent to {to_email} via {mx_server}")
            
            return {
                'success': True,
                'message': 'Email sent successfully',
                'mx_server': mx_server
            }
            
        except smtplib.SMTPRecipientsRefused as e:
            logger.warning(f"Recipient refused: {e}")
            return {
                'success': False,
                'message': 'Recipient refused',
                'bounce': True,
                'bounce_type': 'hard'
            }
            
        except smtplib.SMTPDataError as e:
            logger.warning(f"SMTP data error: {e}")
            return {
                'success': False,
                'message': f'SMTP error: {str(e)}',
                'bounce': False
            }
            
        except Exception as e:
            logger.error(f"SMTP send error: {e}")
            return {
                'success': False,
                'message': f'Send failed: {str(e)}',
                'bounce': False
            }
    
    except Exception as e:
        logger.error(f"Relay error: {e}", exc_info=True)
        return {
            'success': False,
            'message': str(e),
            'bounce': False
        }


def send_email_sync(email_data: dict) -> dict:
    """Synchronous wrapper for async send"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(send_via_relay(email_data))
    finally:
        loop.close()
