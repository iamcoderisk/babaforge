"""
SMTP Relay Server - Sends emails via direct SMTP
"""
import asyncio
import dns.resolver
import logging
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formatdate, make_msgid
from datetime import datetime

logger = logging.getLogger(__name__)


async def send_via_relay(email_data: dict) -> dict:
    """
    Send email via SMTP relay
    """
    to_email = email_data.get('to')
    from_email = email_data.get('from')
    subject = email_data.get('subject', 'No Subject')
    html_body = email_data.get('html_body', '')
    
    try:
        # Get MX records
        domain = to_email.split('@')[1]
        mx_records = dns.resolver.resolve(domain, 'MX')
        mx_records = sorted(mx_records, key=lambda x: x.preference)
        
        # Try each MX server
        for mx in mx_records:
            mx_host = str(mx.exchange).rstrip('.')
            
            try:
                logger.info(f"Trying MX: {mx_host}")
                
                # Create proper MIME message
                msg = MIMEMultipart('alternative')
                msg['From'] = from_email
                msg['To'] = to_email
                msg['Subject'] = subject
                msg['Date'] = formatdate(localtime=True)
                msg['Message-ID'] = make_msgid()
                
                # Create plain text version
                import re
                from html import unescape
                text_body = re.sub('<[^<]+?>', '', html_body)
                text_body = unescape(text_body).strip()
                if not text_body:
                    text_body = subject
                
                # Attach both versions
                msg.attach(MIMEText(text_body, 'plain', 'utf-8'))
                msg.attach(MIMEText(html_body, 'html', 'utf-8'))
                
                # Connect and send
                context = ssl.create_default_context()
                
                with smtplib.SMTP(mx_host, 25, timeout=30) as server:
                    server.ehlo()
                    
                    if server.has_extn('STARTTLS'):
                        server.starttls(context=context)
                        server.ehlo()
                    
                    # Send email
                    server.send_message(msg)
                    
                    logger.info(f"✅ Email sent to {to_email} via {mx_host}")
                    return {
                        'success': True,
                        'message': f'Sent via {mx_host}'
                    }
            
            except Exception as e:
                logger.warning(f"Failed via {mx_host}: {e}")
                continue
        
        return {
            'success': False,
            'error': 'All MX servers failed'
        }
    
    except Exception as e:
        logger.error(f"Relay error: {e}")
        return {
            'success': False,
            'error': str(e)
        }
