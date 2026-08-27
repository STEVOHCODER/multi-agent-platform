import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    Column, String, Integer, Float, Boolean, Text, DateTime,
    ForeignKey, JSON,
)
from app.modules.core.database import Base


def utcnow():
    return datetime.now(timezone.utc)


def gen_uuid():
    return str(uuid.uuid4())


class EmailConnection(Base):
    __tablename__ = "email_connections"

    id = Column(String, primary_key=True, default=gen_uuid)
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    provider = Column(String(50), nullable=False)
    email_address = Column(String(255), nullable=False)
    encrypted_token = Column(Text, nullable=True)
    token_refresh = Column(Text, nullable=True)
    token_expires_at = Column(DateTime, nullable=True)
    imap_host = Column(String(255), nullable=True)
    imap_port = Column(Integer, nullable=True)
    is_active = Column(Boolean, default=True)
    last_sync_at = Column(DateTime, nullable=True)
    last_error = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utcnow)


class WhatsAppConnection(Base):
    __tablename__ = "whatsapp_connections"

    id = Column(String, primary_key=True, default=gen_uuid)
    user_id = Column(String, ForeignKey("users.id"), unique=True, nullable=False)
    phone_number = Column(String(50), nullable=False)
    meta_phone_number_id = Column(String(255), nullable=False)
    meta_access_token = Column(Text, nullable=False)
    is_active = Column(Boolean, default=True)
    last_message_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=utcnow)


class ForwardingRule(Base):
    __tablename__ = "forwarding_rules"

    id = Column(String, primary_key=True, default=gen_uuid)
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    name = Column(String(255), nullable=False, default="Default Rule")
    is_active = Column(Boolean, default=True)
    priority = Column(Integer, default=0)

    sender_emails = Column(JSON, default=list)
    sender_domains = Column(JSON, default=list)
    subject_contains = Column(JSON, default=list)
    body_contains = Column(JSON, default=list)
    has_attachments = Column(Boolean, nullable=True)
    min_importance_score = Column(Integer, default=0)

    forward_to_whatsapp = Column(Boolean, default=True)
    summarize_with_ai = Column(Boolean, default=True)
    custom_message_template = Column(Text, nullable=True)

    created_at = Column(DateTime, default=utcnow)


class MessageLog(Base):
    __tablename__ = "message_logs"

    id = Column(String, primary_key=True, default=gen_uuid)
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    email_connection_id = Column(String, ForeignKey("email_connections.id"), nullable=True)
    whatsapp_connection_id = Column(String, nullable=True)
    email_message_id = Column(String(500), nullable=True)
    email_subject = Column(String(500), nullable=True)
    email_sender = Column(String(255), nullable=True)
    email_received_at = Column(DateTime, nullable=True)
    classification_score = Column(Float, default=0)
    classification_reason = Column(Text, nullable=True)
    summary = Column(Text, nullable=True)
    forwarded = Column(Boolean, default=False)
    whatsapp_message_id = Column(String(255), nullable=True)
    delivery_status = Column(String(50), default="pending")
    delivery_error = Column(Text, nullable=True)
    rule_id = Column(String, ForeignKey("forwarding_rules.id"), nullable=True)
    created_at = Column(DateTime, default=utcnow)


class Usage(Base):
    __tablename__ = "usage"

    id = Column(String, primary_key=True, default=gen_uuid)
    user_id = Column(String, ForeignKey("users.id"), unique=True, nullable=False)
    emails_received = Column(Integer, default=0)
    emails_processed = Column(Integer, default=0)
    messages_forwarded = Column(Integer, default=0)
    messages_failed = Column(Integer, default=0)
    period_start = Column(DateTime, nullable=True)
    period_end = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)
