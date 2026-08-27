from datetime import datetime
from typing import Optional
from pydantic import BaseModel


# Channel
class ChannelCreate(BaseModel):
    channel_type: str
    name: str
    config: dict = {}


class ChannelResponse(BaseModel):
    id: str
    workspace_id: str
    channel_type: str
    name: str
    config: dict
    is_active: bool
    last_message_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


# Contact
class ContactCreate(BaseModel):
    external_id: str = ""
    name: str = ""
    channel_type: str = ""


class ContactResponse(BaseModel):
    id: str
    workspace_id: str
    external_id: Optional[str]
    name: Optional[str]
    channel_type: Optional[str]
    metadata: dict
    created_at: datetime

    class Config:
        from_attributes = True


# Universal Message
class UniversalMessageCreate(BaseModel):
    channel: str
    conversation_id: str
    direction: str = "inbound"
    sender_id: str = ""
    sender_name: str = ""
    text: str = ""
    attachments: list = []
    raw_message: dict = {}


class UniversalMessageResponse(BaseModel):
    id: str
    workspace_id: str
    conversation_id: str
    channel: str
    direction: str
    sender_id: Optional[str]
    sender_name: Optional[str]
    text: Optional[str]
    timestamp: Optional[datetime]
    processed: bool
    agent_id: Optional[str]
    skill_used: Optional[str]
    confidence: Optional[float]
    created_at: datetime

    class Config:
        from_attributes = True


# Conversation
class ConversationResponse(BaseModel):
    id: str
    workspace_id: str
    contact_id: Optional[str]
    channel_type: str
    status: str
    subject: Optional[str]
    last_message_at: Optional[datetime]
    message_count: int
    created_at: datetime

    class Config:
        from_attributes = True


# Memory
class MemoryCreate(BaseModel):
    conversation_id: Optional[str] = None
    memory_type: str = "long_term"
    content: str
    source: str = "observed"
    confidence: float = 0.5
    category: str = ""
    key: str = ""


class MemoryResponse(BaseModel):
    id: str
    workspace_id: str
    conversation_id: Optional[str]
    memory_type: str
    content: str
    source: Optional[str]
    confidence: float
    category: Optional[str]
    key: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True
