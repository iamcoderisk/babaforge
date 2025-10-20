"""
Email Service - Core email sending logic
"""
import json
import uuid
from datetime import datetime
from app import redis_client, db
from app.models.email import Email
from app.services.dkim.dkim_service import DKIMService
from app.config.settings import Config
import logging

logger = logging.getLogger(__name__)

class EmailService:
    """Email sending service"""
    
    def __init__(self):
        self.config = Config()
        self.dkim_service = DKIMService(
            domain=self.config.DOMAIN,
            selector=self.config.DKIM_SELECTOR
        )
    
    def queue_email(self, email_data):
        """Queue email for sending"""
        try:
            # Extract domain
            recipient_email = email_data.get('to')
            domain = recipient_email.split('@')[1] if '@' in recipient_email else 'unknown'
            
            # Create database record
            email = Email(
                id=email_data.get('id', str(uuid.uuid4())),
                batch_id=email_data.get('batch_id'),
                recipient=recipient_email,
                sender=email_data.get('from'),
                subject=email_data.get('subject'),
                status='queued',
                priority=email_data.get('priority', 5),
                domain=domain,
                created_at=datetime.utcnow(),
                queued_at=datetime.utcnow()
            )
            
            db.session.add(email)
            db.session.commit()
            
            # Add to Redis queue
            priority = email_data.get('priority', 5)
            queue_name = f'outgoing_{priority}'
            
            queue_data = {
                'id': email.id,
                'to': recipient_email,
                'from': email_data.get('from'),
                'subject': email_data.get('subject'),
                'text_body': email_data.get('text_body'),
                'html_body': email_data.get('html_body'),
                'headers': email_data.get('headers', {}),
                'priority': priority,
                'domain': domain,
                'created_at': datetime.utcnow().isoformat()
            }
            
            redis_client.lpush(queue_name, json.dumps(queue_data))
            
            logger.info(f"Email {email.id} queued to {recipient_email}")
            
            return {'success': True, 'email_id': email.id}
        
        except Exception as e:
            logger.error(f"Error queuing email: {e}")
            db.session.rollback()
            raise
    
    def get_email_status(self, email_id):
        """Get email status"""
        try:
            email = Email.query.filter_by(id=email_id).first()
            
            if not email:
                return None
            
            return email.to_dict()
        
        except Exception as e:
            logger.error(f"Error getting email status: {e}")
            return None
    
    def get_metrics(self):
        """Get system metrics"""
        try:
            # Get from Redis
            total_sent = redis_client.get('metrics:sent:total') or 0
            total_failed = redis_client.get('metrics:failed:total') or 0
            current_rate = redis_client.get('metrics:send_rate:current') or 0
            
            # Get queue depths
            queue_depths = {}
            total_queued = 0
            for priority in range(1, 11):
                depth = redis_client.llen(f'outgoing_{priority}')
                queue_depths[f'priority_{priority}'] = depth
                total_queued += depth
            
            return {
                'total_sent': int(total_sent),
                'total_failed': int(total_failed),
                'current_rate': int(current_rate),
                'total_queued': total_queued,
                'queues': queue_depths,
                'timestamp': datetime.utcnow().isoformat()
            }
        
        except Exception as e:
            logger.error(f"Error getting metrics: {e}")
            return {}
