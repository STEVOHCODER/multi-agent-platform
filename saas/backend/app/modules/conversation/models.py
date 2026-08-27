import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Boolean, DateTime, Text, JSON, ForeignKey, Integer, Float
from sqlalchemy.orm import relationship
from app.modules.core.database import Base


def utcnow():
    return datetime.now(timezone.utc)


def gen_uuid():
    return str(uuid.uuid4())


class Channel(Base):
    """A communication channel connected to a workspace (WhatsApp, Email, etc.)."""
    __tablename__ = "channels"

    id = Column(String, primary_key=True, default=gen_uuid)
    workspace_id = Column(String, ForeignKey("workspaces.id"), nullable=False, index=True)
    channel_type = Column(String(50), nullable=False)  # whatsapp, email, telegram, sms, webchat
    name = Column(String(255), nullable=False)
    config = Column(JSON, default=dict)  # Provider-specific config (phone number, email address, etc.)
    credentials = Column(JSON, default=dict)  # Encrypted credentials
    is_active = Column(Boolean, default=True)
    last_message_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=utcnow)

    workspace = relationship("Workspace", back_populates="channels")


class Contact(Base):
    """A contact (customer/person) in a workspace."""
    __tablename__ = "contacts"

    id = Column(String, primary_key=True, default=gen_uuid)
    workspace_id = Column(String, ForeignKey("workspaces.id"), nullable=False, index=True)
    external_id = Column(String(255), nullable=True)  # Phone number, email, etc.
    name = Column(String(255), nullable=True)
    channel_type = Column(String(50), nullable=True)  # Last known channel
    extra_data = Column(JSON, default=dict)
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

    workspace = relationship("Workspace", back_populates="contacts")


class Conversation(Base):
    """A conversation thread between agents and a contact."""
    __tablename__ = "conversations"

    id = Column(String, primary_key=True, default=gen_uuid)
    workspace_id = Column(String, ForeignKey("workspaces.id"), nullable=False, index=True)
    contact_id = Column(String, ForeignKey("contacts.id"), nullable=True, index=True)
    channel_id = Column(String, ForeignKey("channels.id"), nullable=True, index=True)
    agent_id = Column(String, ForeignKey("agents.id"), nullable=True, index=True)

    channel_type = Column(String(50), nullable=False)  # whatsapp, email
    external_conversation_id = Column(String(500), nullable=True)  # WhatsApp conversation ID, etc.
    status = Column(String(50), default="active")  # active, closed, archived
    subject = Column(String(500), nullable=True)  # For email threads

    # State
    last_message_at = Column(DateTime, nullable=True)
    message_count = Column(Integer, default=0)
    sentiment = Column(String(50), nullable=True)  # positive, negative, neutral

    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

    workspace = relationship("Workspace", back_populates="conversations")
    messages = relationship("UniversalMessage", back_populates="conversation", cascade="all, delete-orphan")
    memories = relationship("ConversationMemory", back_populates="conversation", cascade="all, delete-orphan")


class UniversalMessage(Base):
    """Canonical message model — all channels produce this."""
    __tablename__ = "universal_messages"

    id = Column(String, primary_key=True, default=gen_uuid)
    workspace_id = Column(String, ForeignKey("workspaces.id"), nullable=False, index=True)
    conversation_id = Column(String, ForeignKey("conversations.id"), nullable=False, index=True)
    channel_id = Column(String, ForeignKey("channels.id"), nullable=True)

    # Universal fields
    channel = Column(String(50), nullable=False)  # whatsapp, email
    direction = Column(String(20), nullable=False)  # inbound, outbound
    sender_id = Column(String(255), nullable=True)
    sender_name = Column(String(255), nullable=True)
    recipient_id = Column(String(255), nullable=True)
    text = Column(Text, nullable=True)
    timestamp = Column(DateTime, nullable=True)

    # Attachments
    attachments = Column(JSON, default=list)

    # Channel-specific raw data
    raw_message = Column(JSON, default=dict)  # Original channel message

    # Processing state
    processed = Column(Boolean, default=False)
    agent_id = Column(String, ForeignKey("agents.id"), nullable=True)
    skill_used = Column(String(255), nullable=True)
    confidence = Column(Float, nullable=True)

    created_at = Column(DateTime, default=utcnow)

    conversation = relationship("Conversation", back_populates="messages")


class ConversationMemory(Base):
    """Short-term and long-term memory for conversations and workspaces."""
    __tablename__ = "conversation_memories"

    id = Column(String, primary_key=True, default=gen_uuid)
    workspace_id = Column(String, ForeignKey("workspaces.id"), nullable=False, index=True)
    conversation_id = Column(String, ForeignKey("conversations.id"), nullable=True, index=True)

    memory_type = Column(String(50), nullable=False)  # short_term, long_term, workspace
    content = Column(Text, nullable=False)
    source = Column(String(100), nullable=True)  # observed, inferred, confirmed
    confidence = Column(Float, default=0.5)
    category = Column(String(100), nullable=True)  # terminology, preference, policy, faq
    key = Column(String(255), nullable=True)  # For workspace memory: lookup key

    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

    conversation = relationship("Conversation", back_populates="memories")
