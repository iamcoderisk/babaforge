"""
Email Worker - Uses Custom SMTP Relay
Run as: python -m app.workers.email_worker 1
"""
import asyncio
import json
import signal
import sys
from datetime import datetime
import redis
import logging

from app.config.settings import Config
from app.smtp.relay_server import send_via_relay

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - Worker-%(process)d - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class EmailWorker:
    """Email worker using custom SMTP relay"""
    
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
        
        signal.signal(signal.SIGINT, self.shutdown)
        signal.signal(signal.SIGTERM, self.shutdown)
    
    def shutdown(self, signum, frame):
        logger.info(f"Worker {self.worker_id} shutting down...")
        self.running = False
    
    async def start(self):
        logger.info(f"🚀 Worker {self.worker_id} started with custom SMTP relay")
        logger.info(f"📧 Ready to send emails directly to recipient MX servers")
        
        while self.running:
            try:
                email_data = None
                
                # Check priority queues (highest first)
                for priority in range(10, 0, -1):
                    queue_name = f'outgoing_{priority}'
                    result = self.redis_client.brpop(queue_name, timeout=1)
                    
                    if result:
                        email_data = json.loads(result[1])
                        break
                
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
        
        try:
            logger.info(f"📤 Worker {self.worker_id} processing email {email_id} to {recipient}")
            
            # Send via custom SMTP relay
            result = await send_via_relay(email_data)
            
            if result['success']:
                logger.info(f"✅ Email {email_id} sent successfully via {result.get('mx_server')}")
                self.processed += 1
                
                if self.processed % 10 == 0:
                    logger.info(f"📊 Worker {self.worker_id}: {self.processed} sent, {self.failed} failed")
            
            elif result.get('bounce'):
                bounce_type = result.get('bounce_type', 'hard')
                logger.warning(f"❌ Email {email_id} bounced ({bounce_type}): {result.get('message')}")
                self.failed += 1
            
            else:
                # Temporary failure - retry
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
                    logger.error(f"💀 Email {email_id} failed after 3 retries: {result.get('message')}")
                    self.redis_client.lpush('dead_letter_queue', json.dumps(email_data))
                    self.failed += 1
        
        except Exception as e:
            logger.error(f"❌ Error processing email {email_id}: {e}")
            self.failed += 1


def main():
    """Entry point"""
    worker_id = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    
    worker = EmailWorker(worker_id)
    asyncio.run(worker.start())


if __name__ == '__main__':
    main()
