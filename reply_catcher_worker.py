#!/usr/bin/env python3
"""
Reply Catcher Worker
Runs SMTP server to capture email replies
"""
import sys
import logging
from app.services.reply_catcher import start_reply_catcher

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

if __name__ == '__main__':
    logger.info("Starting Reply Catcher...")
    
    # Start on port 2525 (or 25 if you have permissions)
    controller = start_reply_catcher(host='0.0.0.0', port=2525)
    
    logger.info("Reply Catcher is running on port 2525")
    logger.info("Press Ctrl+C to stop")
    
    try:
        import asyncio
        asyncio.get_event_loop().run_forever()
    except KeyboardInterrupt:
        logger.info("Shutting down Reply Catcher...")
        controller.stop()
