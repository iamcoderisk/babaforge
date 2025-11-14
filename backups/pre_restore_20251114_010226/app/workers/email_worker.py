"""
Email Worker - Uses Custom SMTP Relay
"""
import asyncio
import json
import signal
import sys
from datetime import datetime
import redis
import logging
import psycopg2

from app.config.settings import Config
from app.smtp.relay_server import send_via_relay

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - Worker-%(process)d - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class EmailWorker:
    """Email worker with database tracking"""
    
    def __init__(self, worker_id=1):
        self.worker_id = worker_id
        self.config = Config()
        self.running = True
        self.redis_client = redis.Redis(
            host=self.config.REDIS_HOST,
            port=self.config.REDIS_PORT,
            decode_responses=True
        )
        self.processed = 0
        self.failed = 0
        
        # Database connection
        self.db_conn = psycopg2.connect(
            host='localhost',
            database='emailer',
            user='emailer',
            password='SecurePassword123'
        )
        
        signal.signal(signal.SIGINT, self.shutdown)
        signal.signal(signal.SIGTERM, self.shutdown)
    
    def shutdown(self, signum, frame):
        logger.info(f"Worker {self.worker_id} shutting down...")
        self.running = False
        if self.db_conn:
            self.db_conn.close()
    
    def update_email_status(self, email_id, status, campaign_id=None):
        """Update email and campaign status in database"""
        try:
            cursor = self.db_conn.cursor()
            
            # Update email status
            cursor.execute(
                "UPDATE emails SET status = %s, updated_at = NOW() WHERE id = %s",
                (status, email_id)
            )
            
            # Update campaign stats if applicable
            if campaign_id and status == 'sent':
                cursor.execute("""
                    UPDATE campaigns 
                    SET emails_sent = COALESCE(emails_sent, 0) + 1,
                        sent_count = COALESCE(sent_count, 0) + 1,
                        status = 'completed',
                        completed_at = NOW()
                    WHERE id = %s
                """, (campaign_id,))
            
            self.db_conn.commit()
            cursor.close()
            
        except Exception as e:
            logger.error(f"Database update error: {e}")
            self.db_conn.rollback()
    
    async def start(self):
        logger.info(f"🚀 Worker {self.worker_id} started with database tracking")
        
        while self.running:
            try:
                email_data = None
                
                # Check priority queues
                for priority in range(10, 0, -1):
                    queue_name = f'outgoing_{priority}'
                    result = self.redis_client.brpop(queue_name, timeout=1)
                    
                    if result:
                        email_data = json.loads(result[1])
                        break
                
                if not email_data:
                    result = self.redis_client.brpop('email_queue', timeout=1)
                    if result:
                        email_data = json.loads(result[1])
                
                if email_data:
                    await self.process_email(email_data)
                else:
                    await asyncio.sleep(0.1)
            
            except Exception as e:
                logger.error(f"Worker {self.worker_id} error: {e}")
                await asyncio.sleep(1)
        
        logger.info(f"Worker {self.worker_id} stopped. Processed: {self.processed}, Failed: {self.failed}")
    
    async def process_email(self, email_data: dict):
        email_id = email_data.get('id')
        recipient = email_data.get('to')
        campaign_id = email_data.get('campaign_id')
        
        try:
            logger.info(f"📤 Worker {self.worker_id} processing email {email_id} to {recipient}")
            
            # Send via SMTP relay
            result = await send_via_relay(email_data)
            
            if result['success']:
                logger.info(f"✅ Email {email_id} sent successfully")
                self.update_email_status(email_id, 'sent', campaign_id)
                self.processed += 1
                
                if self.processed % 10 == 0:
                    logger.info(f"📊 Worker {self.worker_id}: {self.processed} sent, {self.failed} failed")
            
            elif result.get('bounce'):
                logger.warning(f"❌ Email {email_id} bounced")
                self.update_email_status(email_id, 'bounced', campaign_id)
                self.failed += 1
            
            else:
                # Retry logic
                retry_count = email_data.get('retry_count', 0)
                
                if retry_count < 3:
                    email_data['retry_count'] = retry_count + 1
                    priority = email_data.get('priority', 5)
                    
                    self.redis_client.lpush(
                        f"outgoing_{priority}",
                        json.dumps(email_data)
                    )
                    
                    logger.info(f"↻ Email {email_id} requeued (attempt {retry_count + 1}/3)")
                else:
                    logger.error(f"💀 Email {email_id} failed after 3 retries")
                    self.update_email_status(email_id, 'failed', campaign_id)
                    self.failed += 1
        
        except Exception as e:
            logger.error(f"❌ Error processing email {email_id}: {e}")
            self.failed += 1


def main():
    worker_id = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    worker = EmailWorker(worker_id)
    asyncio.run(worker.start())


if __name__ == '__main__':
    main()
