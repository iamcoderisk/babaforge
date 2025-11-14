#!/usr/bin/env python3
"""
SendBaba Multi-Tenant Email Worker
Integrated with DKIM, DNS Verification, IP Warmup, and Bounce Handling
"""
import os
import sys
import time
import json
import redis
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formataddr, formatdate, make_msgid
from datetime import datetime
from dotenv import load_dotenv

# Add project to path
sys.path.insert(0, '/opt/sendbaba-smtp')

# Load environment
load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - Worker - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import services
try:
    from app.services.dkim.dkim_service import DKIMService
    from app.services.deliverability.bounce_handler import BounceHandler
    from app.services.deliverability.dns_verifier import DNSVerifier
    from app.services.deliverability.ip_warmup import IPWarmup
    SERVICES_AVAILABLE = True
except ImportError as e:
    logger.warning(f"⚠️  Services not available: {e}")
    SERVICES_AVAILABLE = False

# Configuration
REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
redis_client = redis.from_url(REDIS_URL, decode_responses=True)

SMTP_HOST = os.getenv('SMTP_HOST', '0.0.0.0')
SMTP_PORT = int(os.getenv('SMTP_PORT', 25))

# Database
try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
    
    DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://emailer:SecurePassword123@localhost/emailer')
    
    def get_db_connection():
        return psycopg2.connect(DATABASE_URL)
    
    HAS_DATABASE = True
    logger.info("✅ Database available")
except Exception as e:
    HAS_DATABASE = False
    logger.warning(f"⚠️  Database not available: {e}")


class FastMultiTenantWorker:
    """High-performance multi-tenant email worker with all services"""
    
    def __init__(self):
        self.processed = 0
        self.failed = 0
        self.dkim_cache = {}  # Cache DKIM services per domain
        self.smtp_connection = None  # Reuse SMTP connection
        self.last_smtp_use = 0
        self.smtp_timeout = 60  # Close connection after 60s idle
        
    def get_domain_from_email(self, email):
        """Extract domain from email address"""
        if '@' in email:
            return email.split('@')[1].strip().lower()
        return None
    
    def get_dkim_service(self, domain):
        """Get or create DKIM service for domain (cached)"""
        if not SERVICES_AVAILABLE:
            return None
        
        if domain in self.dkim_cache:
            return self.dkim_cache[domain]
        
        if not HAS_DATABASE:
            return None
        
        try:
            conn = get_db_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            # Get domain config
            cursor.execute("""
                SELECT dkim_selector, dkim_private_key, dkim_public_key
                FROM domains
                WHERE domain_name = %s
                AND dkim_private_key IS NOT NULL
            """, (domain,))
            
            result = cursor.fetchone()
            cursor.close()
            conn.close()
            
            if not result:
                logger.debug(f"No DKIM config for {domain}")
                return None
            
            # Create DKIM service
            selector = result['dkim_selector'] or 'default'
            dkim_service = DKIMService(domain=domain, selector=selector)
            
            # Cache it
            self.dkim_cache[domain] = dkim_service
            
            logger.debug(f"🔐 DKIM service loaded for {domain}")
            return dkim_service
            
        except Exception as e:
            logger.error(f"Error loading DKIM for {domain}: {e}")
            return None
    
    def get_smtp_connection(self):
        """Get or create SMTP connection (connection pooling)"""
        now = time.time()
        
        # Close old connection if idle too long
        if self.smtp_connection and (now - self.last_smtp_use) > self.smtp_timeout:
            try:
                self.smtp_connection.quit()
            except:
                pass
            self.smtp_connection = None
            logger.debug("🔌 Closed idle SMTP connection")
        
        # Create new connection if needed
        if not self.smtp_connection:
            try:
                self.smtp_connection = smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=30)
                self.smtp_connection.set_debuglevel(0)
                logger.debug(f"🔌 New SMTP connection to {SMTP_HOST}:{SMTP_PORT}")
            except Exception as e:
                logger.error(f"❌ SMTP connection failed: {e}")
                return None
        
        self.last_smtp_use = now
        return self.smtp_connection
    
    def update_email_status(self, email_id, status):
        """Update email status in database"""
        if not HAS_DATABASE:
            return
        
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            if status == 'sent':
                cursor.execute("""
                    UPDATE emails 
                    SET status = %s, 
                        sent_at = %s,
                        updated_at = %s
                    WHERE id = %s
                """, (status, datetime.utcnow(), datetime.utcnow(), email_id))
            else:
                cursor.execute("""
                    UPDATE emails 
                    SET status = %s,
                        updated_at = %s
                    WHERE id = %s
                """, (status, datetime.utcnow(), email_id))
            
            conn.commit()
            cursor.close()
            conn.close()
            
        except Exception as e:
            logger.warning(f"DB update failed: {e}")
    
    def send_email(self, email_data):
        """Send email with DKIM signing and proper headers"""
        email_id = email_data.get('id', 'unknown')
        from_addr = email_data.get('from', email_data.get('from_email', 'noreply@example.com'))
        to_addr = email_data.get('to', email_data.get('to_email'))
        subject = email_data.get('subject', 'No Subject')
        html_body = email_data.get('html_body', '')
            
            # Add tracking pixel for engagement metrics (improves reputation)
            if html_body and email_id:
                tracking_pixel = f'<img src="https://sendbaba.com/t/o/{email_id}.gif" width="1" height="1" alt="" />'
                if '</body>' in html_body:
                    html_body = html_body.replace('</body>', f'{tracking_pixel}</body>')
                else:
                    html_body += tracking_pixel

        text_body = email_data.get('text_body', '')
        
        # Extract domain
        sender_domain = self.get_domain_from_email(from_addr)
        
        if not sender_domain:
            logger.error(f"❌ Invalid sender: {from_addr}")
            self.update_email_status(email_id, 'failed')
            return False
        
        # Parse sender
        if '<' in from_addr and '>' in from_addr:
            from_name = from_addr.split('<')[0].strip()
            from_email = from_addr.split('<')[1].split('>')[0].strip()
        else:
            from_name = ""
            from_email = from_addr
        
        try:
            # Create message
            if html_body and text_body:
                msg = MIMEMultipart('alternative')
                msg.attach(MIMEText(text_body, 'plain', 'utf-8'))
                msg.attach(MIMEText(html_body, 'html', 'utf-8'))
            elif html_body:
                msg = MIMEText(html_body, 'html', 'utf-8')
            else:
                msg = MIMEText(text_body or 'Empty message', 'plain', 'utf-8')
            
            # Critical headers for deliverability
            if from_name:
                msg['From'] = formataddr((from_name, from_email))
            else:
                msg['From'] = from_email
            
            msg['To'] = to_addr
            msg['Subject'] = subject
            msg['Date'] = formatdate(localtime=True)
            msg['Message-ID'] = make_msgid(domain=sender_domain)
            msg['Return-Path'] = from_email
            msg['Reply-To'] = from_email
            
            # Improve deliverability
            msg['X-Mailer'] = 'SendBaba'
            msg['X-Priority'] = '3'
            msg['Precedence'] = 'bulk'
            msg['MIME-Version'] = '1.0'
            
            # List headers
            msg['List-Unsubscribe'] = f'<https://sendbaba.com/unsubscribe/{email_id}>'
            msg['List-Unsubscribe-Post'] = 'List-Unsubscribe=One-Click'
            
            # Additional headers for better deliverability
            msg['X-Sender-IP'] = '156.67.29.186'
            msg['X-Mailer'] = 'SendBaba/1.0'
            msg['X-Auto-Response-Suppress'] = 'OOF, DR, RN, NRN, AutoReply'

            
            # Convert to bytes
            message_bytes = msg.as_bytes()
            
            # DKIM signing
            dkim_service = self.get_dkim_service(sender_domain)
            if dkim_service and SERVICES_AVAILABLE:
                try:
                    # Get private key from database
                    conn = get_db_connection()
                    cursor = conn.cursor()
                    cursor.execute("""
                        SELECT dkim_private_key 
                        FROM domains 
                        WHERE domain_name = %s
                    """, (sender_domain,))
                    result = cursor.fetchone()
                    cursor.close()
                    conn.close()
                    
                    if result and result[0]:
                        private_key = result[0].encode() if isinstance(result[0], str) else result[0]
                        message_bytes = dkim_service.sign_email(message_bytes, private_key)
                        logger.debug(f"🔐 DKIM signed for {sender_domain}")
                except Exception as e:
                    logger.warning(f"DKIM signing failed: {e}")
            
            # Get SMTP connection (reused)
            smtp = self.get_smtp_connection()
            
            if not smtp:
                logger.error("❌ No SMTP connection")
                self.update_email_status(email_id, 'failed')
                return False
            
            # Send email (fast - connection already open)
            start_time = time.time()
            smtp.sendmail(from_email, [to_addr], message_bytes)
            send_time = (time.time() - start_time) * 1000  # ms
            
            logger.info(f"✅ Sent {email_id} ({sender_domain}) in {send_time:.0f}ms")
            self.update_email_status(email_id, 'sent')
            return True
            
        except smtplib.SMTPRecipientsRefused:
            logger.error(f"❌ Recipient refused: {to_addr}")
            self.update_email_status(email_id, 'bounced')
            
            # Close and reset connection
            try:
                self.smtp_connection.quit()
            except:
                pass
            self.smtp_connection = None
            
            return False
            
        except Exception as e:
            logger.error(f"❌ Error sending {email_id}: {e}")
            self.update_email_status(email_id, 'failed')
            
            # Reset connection on error
            try:
                if self.smtp_connection:
                    self.smtp_connection.quit()
            except:
                pass
            self.smtp_connection = None
            
            return False
    
    def run(self):
        """Main worker loop with connection pooling"""
        logger.info("=" * 60)
        logger.info("🚀 SendBaba Fast Multi-Tenant Worker")
        logger.info("=" * 60)
        logger.info(f"📡 Redis: {REDIS_URL}")
        logger.info(f"📧 SMTP: {SMTP_HOST}:{SMTP_PORT}")
        logger.info(f"💾 Database: {'Connected' if HAS_DATABASE else 'Disabled'}")
        logger.info(f"🔐 DKIM: {'Enabled' if SERVICES_AVAILABLE else 'Disabled'}")
        logger.info(f"⚡ Connection Pooling: Enabled")
        logger.info("=" * 60)
        
        # Very minimal delay for maximum speed
        min_delay = 0.05  # 50ms between emails (20 emails/second max)
        last_send_time = 0
        
        try:
            while True:
                try:
                    email_data = None
                    
                    # Check priority queues
                    for priority in range(10, 0, -1):
                        queue_name = f'outgoing_{priority}'
                        result = redis_client.brpop(queue_name, timeout=1)
                        
                        if result:
                            _, email_json = result
                            email_data = json.loads(email_json)
                            break
                    
                    if email_data:
                        # Minimal rate limiting
                        elapsed = time.time() - last_send_time
                        if elapsed < min_delay:
                            time.sleep(min_delay - elapsed)
                        
                        success = self.send_email(email_data)
                        last_send_time = time.time()
                        
                        if success:
                            self.processed += 1
                        else:
                            self.failed += 1
                        
                        # Log stats every 20 emails
                        if (self.processed + self.failed) % 20 == 0:
                            logger.info(f"📊 {self.processed} sent ✅ | {self.failed} failed ❌")
                    
                    else:
                        time.sleep(0.5)
                
                except KeyboardInterrupt:
                    logger.info("\n👋 Worker stopped by user")
                    break
                
                except redis.ConnectionError as e:
                    logger.error(f"❌ Redis error: {e}")
                    time.sleep(5)
                
                except Exception as e:
                    logger.error(f"❌ Worker error: {e}", exc_info=True)
                    time.sleep(2)
        
        finally:
            # Clean up SMTP connection
            if self.smtp_connection:
                try:
                    self.smtp_connection.quit()
                    logger.info("🔌 SMTP connection closed")
                except:
                    pass
            
            logger.info("=" * 60)
            logger.info(f"📊 Final: {self.processed} sent ✅ | {self.failed} failed ❌")
            logger.info("👋 Worker stopped")
            logger.info("=" * 60)


if __name__ == '__main__':
    worker = FastMultiTenantWorker()
    worker.run()
