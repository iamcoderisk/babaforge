"""
SendBaba Python SDK
Official Python client for the SendBaba API
"""

__version__ = '1.0.0'

from .client import SendBaba
from .exceptions import (
    SendBabaError,
    AuthenticationError,
    RateLimitError,
    ValidationError,
    NotFoundError
)

__all__ = [
    'SendBaba',
    'SendBabaError',
    'AuthenticationError',
    'RateLimitError',
    'ValidationError',
    'NotFoundError'
]
