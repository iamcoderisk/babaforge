"""
Database Models and Schema
SQLAlchemy ORM models for all entities
"""
from datetime import datetime
from typing import Optional, List
from sqlalchemy import (
    Column, Integer, String, Text, Boolean, DateTime, 
    Float, BigInteger, ForeignKey, Index, JSON, LargeBinary
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
import uuid

Base = declarative_base()

class Organization(Base):
    """Multi-tenant organization model"""
    __tablename__ = 'organizations'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    uuid = Column(UUID(as_uuid=True), unique=True, default=uuid.uuid4, nullable=False)
    name = Column(String(255), unique=True, nullable=False, index=True)
    api_key = Column(String(255), unique=True, nullable=False, index=True)
    status = Column(String(50), default='active', nullable=False)
    
    # Limits
    max_emails_per_second = Column(Integer, default=1000)
    max_emails_per_minute = Column(Integer, default=50000)
    max_emails_per_hour = Column(Integer, default=1000000)
    max_email_size = Column(BigInteger, default=25*1024*1024)
    
    # Features
    features = Column(JSONB, default={})
    metadata_ = Column('metadata', JSONB, default={})
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    domains = relationship("Domain", back_populates="organization", cascade="all, delete-orphan")
    emails_outgoing = relationship("EmailOutgoing", back_populates="organization")
    emails_incoming = relationship("EmailIncoming", back_populates="organization")
    
    __table_args__ = (
        Index('idx_org_status', 'status'),
        Index('idx_org_created', 'created_at'),
    )

class Domain(Base):
    """Email domains for sending/receiving"""
    __tablename__ = 'domains'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    org_id = Column(Integer, ForeignKey('organizations.id'), nullable=False)
    domain = Column(String(255), nullable=False, index=True)
    
    # DNS Records
    dkim_selector = Column(String(100), default='default')
    dkim_public_key = Column(Text)
    spf_record = Column(Text)
    dmarc_record = Column(Text)
    
    # Verification
    verified = Column(Boolean, default=False)
    verified_at = Column(DateTime)
    verification_token = Column(String(255))
    
    # Reverse DNS
    reverse_dns = Column(String(255))
    reverse_dns_verified = Column(Boolean, default=False)
    
    # IP Pool
    ip_pool_id = Column(Integer, ForeignKey('ip_pools.id'))
    
    # Status
    status = Column(String(50), default='pending')
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    organization = relationship("Organization", back_populates="domains")
    ip_pool = relationship("IPPool", back_populates="domains")
    
    __table_args__ = (
        Index('idx_domain_org', 'org_id', 'domain'),
        Index('idx_domain_verified', 'verified'),
    )

class IPPool(Base):
    """IP address pools for sending"""
    __tablename__ = 'ip_pools'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    org_id = Column(Integer, ForeignKey('organizations.id'), nullable=False)
    name = Column(String(255), nullable=False)
    ip_addresses = Column(ARRAY(String), nullable=False)
    
    # Rotation strategy
    rotation_strategy = Column(String(50), default='round_robin')
    current_index = Column(Integer, default=0)
    
    # Warmup
    warmup_enabled = Column(Boolean, default=True)
    warmup_daily_limit = Column(Integer, default=5000)
    
    # Reputation
    reputation_score = Column(Float, default=100.0)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    domains = relationship("Domain", back_populates="ip_pool")

class EmailOutgoing(Base):
    """Outgoing emails"""
    __tablename__ = 'emails_outgoing'
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    org_id = Column(Integer, ForeignKey('organizations.id'), nullable=False, index=True)
    message_id = Column(String(255), unique=True, nullable=False, index=True)
    
    # Email details
    sender = Column(String(255), nullable=False, index=True)
    recipients = Column(ARRAY(String), nullable=False)
    subject = Column(Text)
    body_text = Column(Text)
    body_html = Column(Text)
    
    # Headers
    headers = Column(JSONB, default={})
    
    # Attachments
    attachments = Column(JSONB, default=[])
    
    # Processing
    status = Column(String(50), default='queued', nullable=False, index=True)
    priority = Column(Integer, default=5)
    queue_name = Column(String(100), default='default')
    
    # Delivery
    delivered_at = Column(DateTime)
    bounced_at = Column(DateTime)
    bounce_type = Column(String(50))
    bounce_reason = Column(Text)
    
    # Tracking
    opened = Column(Boolean, default=False)
    opened_at = Column(DateTime)
    open_count = Column(Integer, default=0)
    clicked = Column(Boolean, default=False)
    clicked_at = Column(DateTime)
    click_count = Column(Integer, default=0)
    
    # DKIM
    dkim_signed = Column(Boolean, default=False)
    dkim_signature = Column(Text)
    
    # IP & DNS
    sending_ip = Column(String(45))
    reverse_dns = Column(String(255))
    
    # Metadata
    tags = Column(ARRAY(String), default=[])
    metadata_ = Column('metadata', JSONB, default={})
    
    # Retry
    attempt_count = Column(Integer, default=0)
    max_attempts = Column(Integer, default=3)
    next_retry_at = Column(DateTime)
    
    # Size
    message_size = Column(BigInteger)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    organization = relationship("Organization", back_populates="emails_outgoing")
    
    __table_args__ = (
        Index('idx_email_out_org_created', 'org_id', 'created_at'),
        Index('idx_email_out_status', 'status'),
        Index('idx_email_out_retry', 'next_retry_at'),
        Index('idx_email_out_sender', 'sender'),
    )

class EmailIncoming(Base):
    """Incoming emails"""
    __tablename__ = 'emails_incoming'
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    org_id = Column(Integer, ForeignKey('organizations.id'), nullable=False, index=True)
    message_id = Column(String(255), unique=True, nullable=False, index=True)
    
    # Email details
    sender = Column(String(255), nullable=False, index=True)
    recipients = Column(ARRAY(String), nullable=False)
    subject = Column(Text)
    body_text = Column(Text)
    body_html = Column(Text)
    
    # Headers
    headers = Column(JSONB, default={})
    
    # Attachments
    attachments = Column(JSONB, default=[])
    
    # Verification
    dkim_valid = Column(Boolean, default=False)
    spf_valid = Column(Boolean, default=False)
    dmarc_valid = Column(Boolean, default=False)
    
    # Spam
    spam_score = Column(Float, default=0.0)
    spam_checked = Column(Boolean, default=False)
    is_spam = Column(Boolean, default=False)
    
    # Virus
    virus_checked = Column(Boolean, default=False)
    has_virus = Column(Boolean, default=False)
    
    # Processing
    status = Column(String(50), default='received')
    processed = Column(Boolean, default=False)
    processed_at = Column(DateTime)
    
    # Metadata
    tags = Column(ARRAY(String), default=[])
    metadata_ = Column('metadata', JSONB, default={})
    
    # Size
    message_size = Column(BigInteger)
    
    # Raw message (compressed)
    raw_message = Column(LargeBinary)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Relationships
    organization = relationship("Organization", back_populates="emails_incoming")
    
    __table_args__ = (
        Index('idx_email_in_org_created', 'org_id', 'created_at'),
        Index('idx_email_in_sender', 'sender'),
        Index('idx_email_in_spam', 'is_spam'),
    )

class Webhook(Base):
    """Webhook configurations"""
    __tablename__ = 'webhooks'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    org_id = Column(Integer, ForeignKey('organizations.id'), nullable=False)
    url = Column(Text, nullable=False)
    event_types = Column(ARRAY(String), nullable=False)
    
    # Authentication
    secret = Column(String(255))
    headers = Column(JSONB, default={})
    
    # Status
    active = Column(Boolean, default=True)
    
    # Stats
    total_calls = Column(BigInteger, default=0)
    failed_calls = Column(BigInteger, default=0)
    last_called_at = Column(DateTime)
    last_error = Column(Text)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_webhook_org', 'org_id'),
    )

class SuppressionList(Base):
    """Email suppression list"""
    __tablename__ = 'suppression_lists'
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    org_id = Column(Integer, ForeignKey('organizations.id'), nullable=False)
    email = Column(String(255), nullable=False, index=True)
    
    # Reason
    reason = Column(String(100), nullable=False)
    bounce_type = Column(String(50))
    
    # Source
    added_by = Column(String(50), default='system')
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime)
    
    __table_args__ = (
        Index('idx_suppression_org_email', 'org_id', 'email', unique=True),
    )

class Analytics(Base):
    """Real-time analytics aggregation"""
    __tablename__ = 'analytics'
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    org_id = Column(Integer, ForeignKey('organizations.id'), nullable=False, index=True)
    
    # Time bucket
    bucket_timestamp = Column(DateTime, nullable=False, index=True)
    bucket_size = Column(String(20), default='hour')
    
    # Metrics
    emails_sent = Column(BigInteger, default=0)
    emails_delivered = Column(BigInteger, default=0)
    emails_bounced = Column(BigInteger, default=0)
    emails_opened = Column(BigInteger, default=0)
    emails_clicked = Column(BigInteger, default=0)
    emails_spam = Column(BigInteger, default=0)
    
    # Rates
    delivery_rate = Column(Float, default=0.0)
    bounce_rate = Column(Float, default=0.0)
    open_rate = Column(Float, default=0.0)
    click_rate = Column(Float, default=0.0)
    
    # By domain
    by_domain = Column(JSONB, default={})
    
    # By tag
    by_tag = Column(JSONB, default={})
    
    __table_args__ = (
        Index('idx_analytics_org_bucket', 'org_id', 'bucket_timestamp'),
    )
