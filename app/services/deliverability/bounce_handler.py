"""
Advanced Bounce Handling System
Processes bounce emails and manages suppression lists
"""
import re
from datetime import datetime, timedelta
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)


class BounceHandler:
    """Handle email bounces and complaints"""
    
    # Bounce type patterns
    HARD_BOUNCE_PATTERNS = [
        r'user.*unknown',
        r'account.*disabled',
        r'mailbox.*not.*found',
        r'no.*such.*user',
        r'recipient.*rejected',
        r'address.*rejected',
        r'550.*5\.1\.1',  # User unknown
        r'551.*5\.1\.1',  # User not local
        r'554.*5\.7\.1',  # Relay denied
    ]
    
    SOFT_BOUNCE_PATTERNS = [
        r'mailbox.*full',
        r'quota.*exceeded',
        r'temporarily.*unavailable',
        r'try.*again.*later',
        r'451.*4\.2\.2',  # Mailbox full
        r'452.*4\.2\.2',  # Insufficient storage
        r'421.*4\.4\.2',  # Timeout
    ]
    
    SPAM_PATTERNS = [
        r'spam.*detected',
        r'554.*5\.7\.1.*spam',
        r'blocked.*spam',
        r'content.*rejected',
    ]
    
    def __init__(self, db_session):
        self.db = db_session
    
    def process_bounce(self, email_id: str, bounce_message: str) -> Dict:
        """
        Process bounce notification
        Returns: {
            'type': 'hard'|'soft'|'spam'|'unknown',
            'action': 'suppress'|'retry'|'none',
            'reason': str
        }
        """
        bounce_message = bounce_message.lower()
        
        # Detect bounce type
        if self._matches_patterns(bounce_message, self.HARD_BOUNCE_PATTERNS):
            return {
                'type': 'hard',
                'action': 'suppress',
                'reason': 'Hard bounce - email address invalid'
            }
        
        elif self._matches_patterns(bounce_message, self.SOFT_BOUNCE_PATTERNS):
            return {
                'type': 'soft',
                'action': 'retry',
                'reason': 'Soft bounce - temporary issue'
            }
        
        elif self._matches_patterns(bounce_message, self.SPAM_PATTERNS):
            return {
                'type': 'spam',
                'action': 'suppress',
                'reason': 'Marked as spam by recipient server'
            }
        
        return {
            'type': 'unknown',
            'action': 'none',
            'reason': 'Unknown bounce reason'
        }
    
    def _matches_patterns(self, message: str, patterns: list) -> bool:
        """Check if message matches any pattern"""
        return any(re.search(pattern, message) for pattern in patterns)
    
    def add_to_suppression(self, email: str, reason: str, bounce_type: str):
        """Add email to suppression list"""
        from app.models.suppression import SuppressionList
        
        suppression = SuppressionList(
            email=email.lower(),
            reason=reason,
            type=bounce_type,
            added_at=datetime.utcnow()
        )
        
        self.db.add(suppression)
        self.db.commit()
        
        logger.info(f"Added {email} to suppression list: {reason}")
    
    def check_suppressed(self, email: str) -> Optional[Dict]:
        """Check if email is suppressed"""
        from app.models.suppression import SuppressionList
        
        suppressed = SuppressionList.query.filter_by(
            email=email.lower()
        ).first()
        
        if suppressed:
            return {
                'suppressed': True,
                'reason': suppressed.reason,
                'type': suppressed.type,
                'added_at': suppressed.added_at
            }
        
        return None
    
    def remove_from_suppression(self, email: str):
        """Remove email from suppression list"""
        from app.models.suppression import SuppressionList
        
        SuppressionList.query.filter_by(email=email.lower()).delete()
        self.db.commit()
        
        logger.info(f"Removed {email} from suppression list")
