"""
Enhanced Email Worker - Fixed version
"""
import asyncio
import json
import signal
import sys
import os
from datetime import datetime
import redis
import logging

# Add project to path
sys.path.insert(0, '/opt/sendbaba-smtp')

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - Worker - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import after path is set
from app.smtp.relay_server import send_via_relay


class SimpleEmailWorker:
    """Simple, reliable email worker"""
    
    def __init__(self):
        self.running = True
        self.processed = 0
        
        # Redis
        self.redis_client = redis.Redis(
            host=os.getenv('REDIS_HOST', 'localhost'),
            port=int(os.getenv('REDIS_PORT', 6379)),
            decode_responses=True
        )
        
        # Signal handlers
        signal.signal(signal.SIGINT, self.shutdown)
        signal.signal(signal.SIGTERM, self.shutdown)
        
        logger.info("✅ Simple Worker initialized")
    
    def shutdown(self, signum, frame):
        logger.info("Worker shutting down...")
        self.running = False
    
    async def process_email(self, email_data: dict):
        """Process single email"""
        email_id = email_data.get('id')
        recipient = email_data.get('to')
        
        try:
            logger.info(f"📤 Sending to {recipient}")
            
            # Send email
            result = await send_via_relay(email_data)
            
            if result['success']:
                self.processed += 1
                logger.info(f"✅ Sent to {recipient}")
                
                # Try to update database, but don't fail if it doesn't work
                try:
                    self.update_status(email_id, 'sent')
                except Exception as db_error:
                    logger.warning(f"Could not update DB (email was sent): {db_error}")
                
                return True
            else:
                # Retry logic
                retry_count = email_data.get('retry_count', 0)
                if retry_count < 3:
                    email_data['retry_count'] = retry_count + 1
                    self.redis_client.lpush('outgoing_10', json.dumps(email_data))
                    logger.info(f"↻ Requeued (attempt {retry_count + 1}/3)")
                else:
                    logger.error(f"❌ Failed after 3 retries")
                    try:
                        self.update_status(email_id, 'failed')
                    except:
                        pass
                
                return False
        
        except Exception as e:
            logger.error(f"Error processing email: {e}")
            return False
    
    def update_status(self, email_id: str, status: str):
        """Update email status in database"""
        try:
            import psycopg2
            
            conn = psycopg2.connect(
                host='localhost',
                database='emailer',
                user='emailer',
                password='SecurePassword123'
            )
            
            cursor = conn.cursor()
            
            if status == 'sent':
                cursor.execute(
                    "UPDATE emails SET status = %s, sent_at = %s WHERE id = %s",
                    (status, datetime.utcnow(), email_id)
                )
            else:
                cursor.execute(
                    "UPDATE emails SET status = %s WHERE id = %s",
                    (status, email_id)
                )
            
            conn.commit()
            cursor.close()
            conn.close()
            
        except Exception as e:
            logger.warning(f"DB update failed: {e}")
    
    async def start(self):
        """Start the worker"""
        logger.info("🚀 Worker started - waiting for emails...")
        
        while self.running:
            try:
                # Check priority queues
                email_data = None
                for priority in range(10, 0, -1):
                    queue_name = f'outgoing_{priority}'
                    result = self.redis_client.brpop(queue_name, timeout=1)
                    
                    if result:
                        email_data = json.loads(result[1])
                        break
                
                if email_data:
                    await self.process_email(email_data)
                else:
                    await asyncio.sleep(1)
                
                # Log stats every 10 emails
                if self.processed % 10 == 0 and self.processed > 0:
                    logger.info(f"📊 Processed: {self.processed}")
            
            except Exception as e:
                logger.error(f"Worker loop error: {e}")
                await asyncio.sleep(1)
        
        logger.info(f"Worker stopped. Processed: {self.processed}")


def main():
    """Entry point"""
    worker = SimpleEmailWorker()
    asyncio.run(worker.start())


if __name__ == '__main__':
    main()
