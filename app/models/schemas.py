from pydantic import BaseModel, EmailStr, Field, validator
from typing import List, Optional, Dict, Any
from datetime import datetime

class EmailSendRequest(BaseModel):
    """Request schema for sending email"""
    to: List[EmailStr] = Field(..., min_items=1, max_items=1000)
    subject: str = Field(..., min_length=1, max_length=998)
    body_text: Optional[str] = None
    body_html: Optional[str] = None
    from_email: Optional[EmailStr] = None
    from_name: Optional[str] = None
    reply_to: Optional[EmailStr] = None
    cc: Optional[List[EmailStr]] = None
    bcc: Optional[List[EmailStr]] = None
    attachments: Optional[List[Dict[str, Any]]] = None
    headers: Optional[Dict[str, str]] = None
    tags: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None
    priority: int = Field(default=5, ge=1, le=10)
    send_at: Optional[datetime] = None
    
    @validator('body_text', 'body_html')
    def validate_body(cls, v, values):
        if not v and not values.get('body_html') and not values.get('body_text'):
            raise ValueError('Either body_text or body_html must be provided')
        return v

class EmailBatchRequest(BaseModel):
    """Batch email send request"""
    emails: List[EmailSendRequest] = Field(..., min_items=1, max_items=10000)

class EmailResponse(BaseModel):
    """Email send response"""
    message_id: str
    status: str
    queued_at: datetime

class OrganizationCreate(BaseModel):
    """Create organization"""
    name: str = Field(..., min_length=1, max_length=255)
    max_emails_per_hour: int = Field(default=1000000, ge=1)
    
class DomainCreate(BaseModel):
    """Create domain"""
    domain: str = Field(..., regex=r'^[a-zA-Z0-9][a-zA-Z0-9-]{0,61}[a-zA-Z0-9]?\.[a-zA-Z]{2,}$')
    ip_pool_id: Optional[int] = None

class WebhookCreate(BaseModel):
    """Create webhook"""
    url: str = Field(..., regex=r'^https?://')
    event_types: List[str] = Field(..., min_items=1)
    secret: Optional[str] = None
    headers: Optional[Dict[str, str]] = None
