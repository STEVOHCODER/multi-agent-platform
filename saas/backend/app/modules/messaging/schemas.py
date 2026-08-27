from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel


# Email Connections
class EmailConnect(BaseModel):
    provider: str
    email_address: str
    password: Optional[str] = None
    imap_host: Optional[str] = None
    imap_port: Optional[int] = None


class EmailConnectionResponse(BaseModel):
    id: str
    provider: str
    email_address: str
    is_active: bool
    last_sync_at: Optional[datetime]
    last_error: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


# WhatsApp
class WhatsAppConnect(BaseModel):
    phone_number: str
    meta_phone_number_id: str
    meta_access_token: str


class WhatsAppResponse(BaseModel):
    id: str
    phone_number: str
    is_active: bool
    last_message_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


# Forwarding Rules
class RuleCreate(BaseModel):
    name: str = "Default Rule"
    sender_emails: List[str] = []
    sender_domains: List[str] = []
    subject_contains: List[str] = []
    body_contains: List[str] = []
    has_attachments: Optional[bool] = None
    min_importance_score: int = 0
    forward_to_whatsapp: bool = True
    summarize_with_ai: bool = True


class RuleUpdate(BaseModel):
    name: Optional[str] = None
    is_active: Optional[bool] = None
    sender_emails: Optional[List[str]] = None
    sender_domains: Optional[List[str]] = None
    subject_contains: Optional[List[str]] = None
    body_contains: Optional[List[str]] = None
    has_attachments: Optional[bool] = None
    min_importance_score: Optional[int] = None
    forward_to_whatsapp: Optional[bool] = None
    summarize_with_ai: Optional[bool] = None


class RuleResponse(BaseModel):
    id: str
    name: str
    is_active: bool
    sender_emails: List[str]
    sender_domains: List[str]
    subject_contains: List[str]
    body_contains: List[str]
    has_attachments: Optional[bool]
    min_importance_score: int
    forward_to_whatsapp: bool
    summarize_with_ai: bool
    created_at: datetime

    class Config:
        from_attributes = True


# Message Logs
class MessageLogResponse(BaseModel):
    id: str
    email_subject: Optional[str]
    email_sender: Optional[str]
    email_received_at: Optional[datetime]
    classification_score: float
    summary: Optional[str]
    forwarded: bool
    delivery_status: str
    delivery_error: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


# Dashboard
class DashboardResponse(BaseModel):
    status: str
    email_connections: int
    whatsapp_connected: bool
    messages_today: int
    messages_this_month: int
    plan: str
    recent_messages: List[MessageLogResponse]


# Usage
class UsageResponse(BaseModel):
    emails_received: int
    emails_processed: int
    messages_forwarded: int
    messages_failed: int
    period_start: Optional[datetime]
    period_end: Optional[datetime]

    class Config:
        from_attributes = True
