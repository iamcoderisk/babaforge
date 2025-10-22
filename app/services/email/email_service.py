"""
Email Service - Queue Management
"""
import json
import redis
import logging
from app.config.settings import Config

logger = logging.getLogger(__name__)

class EmailService:
    """Email service for queueing and status tracking"""
    
    def __init__(self):
        self.config = Config()
        # FIXED: Use decode_responses=False to handle bytes properly
        self.redis_client = redis.Redis(
            host=self.config.REDIS_HOST,
            port=self.config.REDIS_PORT,
            db=self.config.REDIS_DB,
            decode_responses=False  # Changed to False
        )
        # Test connection on init
        try:
            self.redis_client.ping()
            logger.info("Redis connection established successfully")
        except Exception as e:
            logger.error(f"Redis connection failed: {e}")
    def queue_email(self, email_data):
        """Queue email for sending"""
        try:
            # Ensure all required fields are present
            email_payload = {
                'id': email_data.get('id'),
                'from': email_data.get('from'),
                'to': email_data.get('to'),
                'subject': email_data.get('subject'),
                'text_body': email_data.get('text_body', ''),
                'html_body': email_data.get('html_body'),
                'priority': email_data.get('priority', 5),
                'headers': email_data.get('headers', {}),
                'batch_id': email_data.get('batch_id')
            }
            
            # Remove None values
            email_payload = {k: v for k, v in email_payload.items() if v is not None}
            
            # Try to save to database (but don't fail if it errors)
            try:
                from app import db
                from app.models.database import EmailOutgoing
                from datetime import datetime
                
                # Check if record already exists
                existing = EmailOutgoing.query.filter_by(message_id=email_payload['id']).first()
                
                if not existing:
                    email_record = EmailOutgoing(
                        message_id=email_payload['id'],
                        org_id=1,  # Default organization
                        sender=email_payload['from'],
                        recipients=[email_payload['to']],
                        subject=email_payload['subject'],
                        body_text=email_payload.get('text_body', ''),
                        body_html=email_payload.get('html_body'),
                        status='queued',
                        priority=email_payload.get('priority', 5),
                        headers=email_payload.get('headers', {}),
                        created_at=datetime.utcnow()
                    )
                    
                    db.session.add(email_record)
                    db.session.commit()
                    logger.info(f"Email {email_payload['id']} saved to database")
                else:
                    logger.info(f"Email {email_payload['id']} already exists in database")
                    
            except Exception as db_error:
                logger.warning(f"Database save failed (continuing anyway): {db_error}")
                try:
                    db.session.rollback()
                except:
                    pass
            
            # Convert to JSON and encode to bytes
            email_json = json.dumps(email_payload)
            
            # Add to Redis queue
            result = self.redis_client.lpush('email_queue', email_json.encode('utf-8'))
            
            logger.info(f"Email {email_payload['id']} queued to Redis (queue length: {result})")
            
            return {
                'success': True,
                'queue': 'email_queue',
                'queue_length': result
            }
            
        except Exception as e:
            logger.error(f"Error queueing email: {e}")
            import traceback
            logger.error(traceback.format_exc())
            raise
    # def queue_email(self, email_data):
    #     """Queue email for sending - uses same queue as working Redis test"""
    #     try:
    #         # Ensure all required fields are present
    #         email_payload = {
    #             'id': email_data.get('id'),
    #             'from': email_data.get('from'),
    #             'to': email_data.get('to'),
    #             'subject': email_data.get('subject'),
    #             'text_body': email_data.get('text_body', ''),
    #             'html_body': email_data.get('html_body'),
    #             'priority': email_data.get('priority', 5),
    #             'headers': email_data.get('headers', {}),
    #             'batch_id': email_data.get('batch_id')
    #         }
            
    #         # Remove None values
    #         email_payload = {k: v for k, v in email_payload.items() if v is not None}
            
    #         # Convert to JSON and encode to bytes
    #         email_json = json.dumps(email_payload)
            
    #         # Add to the SAME queue that works with TLS
    #         # LPUSH returns the new length of the list
    #         result = self.redis_client.lpush('email_queue', email_json.encode('utf-8'))
            
    #         logger.info(f"Email {email_payload['id']} queued successfully to email_queue (queue length: {result})")
            
    #         return {
    #             'success': True,
    #             'queue': 'email_queue',
    #             'queue_length': result
    #         }
            
    #     except Exception as e:
    #         logger.error(f"Error queueing email: {e}")
    #         import traceback
    #         logger.error(traceback.format_exc())
    #         raise
    
    def get_email_status(self, email_id):
        """Get email status from database"""
        try:
            from app import db
            from app.models.database import EmailOutgoing
            
            email = EmailOutgoing.query.filter_by(message_id=email_id).first()
            if email:
                return {
                    'status': email.status,
                    'created_at': email.created_at.isoformat() if email.created_at else None,
                    'delivered_at': email.delivered_at.isoformat() if email.delivered_at else None,
                    'to': email.recipients[0] if email.recipients else None,
                    'from': email.sender,
                    'subject': email.subject
                }
            return None
            
        except Exception as e:
            logger.error(f"Error getting email status: {e}")
            return None
    
    def get_metrics(self):
        """Get system metrics from Redis"""
        try:
            # Decode responses when getting metrics
            total_sent = self.redis_client.get('metrics:sent:total')
            total_bounced = self.redis_client.get('metrics:bounced:total')
            
            metrics = {
                'total_sent': int(total_sent.decode('utf-8') if total_sent else 0),
                'total_bounced': int(total_bounced.decode('utf-8') if total_bounced else 0),
                'queue_depths': {}
            }
            
            # Get queue depths
            for priority in range(1, 11):
                queue_name = f'outgoing_{priority}'
                depth = self.redis_client.llen(queue_name)
                if depth > 0:
                    metrics['queue_depths'][queue_name] = depth
            
            # Check email_queue too
            email_queue_depth = self.redis_client.llen('email_queue')
            if email_queue_depth > 0:
                metrics['queue_depths']['email_queue'] = email_queue_depth
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error getting metrics: {e}")
            return {}