import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler

from app.config.settings import settings

def setup_logging():
    """Setup application logging"""
    
    # Create logs directory
    Path(settings.LOG_FILE).parent.mkdir(parents=True, exist_ok=True)
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # File handler
    file_handler = RotatingFileHandler(
        settings.LOG_FILE,
        maxBytes=settings.LOG_MAX_SIZE,
        backupCount=settings.LOG_BACKUP_COUNT
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(settings.LOG_LEVEL)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(settings.LOG_LEVEL)
    
    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(settings.LOG_LEVEL)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)

def get_logger(name: str) -> logging.Logger:
    """Get logger instance"""
    return logging.getLogger(name)