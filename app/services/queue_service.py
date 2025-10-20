import aio_pika
import json
from typing import Dict, Any

from app.config.settings import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)

class QueueService:
    """RabbitMQ queue service"""
    
    def __init__(self):
        self.connection = None
        self.channel = None
    
    async def connect(self):
        """Connect to RabbitMQ"""
        if not self.connection:
            self.connection = await aio_pika.connect_robust(settings.RABBITMQ_URL)
            self.channel = await self.connection.channel()
            await self.channel.set_qos(prefetch_count=settings.BATCH_SIZE)
            logger.info("Connected to RabbitMQ")
    
    async def enqueue_email(self, email):
        """Add email to outgoing queue"""
        await self.connect()
        
        queue_name = f"outgoing_{email.priority}"
        queue = await self.channel.declare_queue(queue_name, durable=True)
        
        message_body = json.dumps({
            'email_id': email.id,
            'message_id': email.message_id,
            'org_id': email.org_id,
            'priority': email.priority
        })
        
        await self.channel.default_exchange.publish(
            aio_pika.Message(
                body=message_body.encode(),
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT
            ),
            routing_key=queue_name
        )
        
        logger.debug(f"Enqueued email {email.message_id}")
    
    async def consume_emails(self, callback):
        """Consume emails from queue"""
        await self.connect()
        
        # Create queues for different priorities
        for priority in range(1, 11):
            queue_name = f"outgoing_{priority}"
            queue = await self.channel.declare_queue(queue_name, durable=True)
            await queue.consume(callback)
        
        logger.info("Started consuming from queues")
