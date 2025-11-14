"""
Bounce Receiver - Standalone Script
Run as: sudo python -m app.smtp.bounce_receiver
"""
import asyncio
import sys
import os
import logging

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.smtp.relay_server import SMTPBounceReceiver

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def main():
    """Start bounce receiver"""
    logger.info("Starting SMTP Bounce Receiver on port 25...")
    logger.info("This receives bounce-back messages from mail servers")
    
    receiver = SMTPBounceReceiver(
        listen_ip='0.0.0.0',
        listen_port=25,
        domain='sendbaba.com'
    )
    
    try:
        await receiver.start()
    except PermissionError:
        logger.error("❌ Permission denied. Port 25 requires root privileges.")
        logger.error("Run as: sudo python -m app.smtp.bounce_receiver")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Error starting bounce receiver: {e}")
        sys.exit(1)


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bounce receiver stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)
