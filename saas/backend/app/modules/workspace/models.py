import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from app.modules.core.database import Base


def utcnow():
    return datetime.now(timezone.utc)


def gen_uuid():
    return str(uuid.uuid4())


class Workspace(Base):
    __tablename__ = "workspaces"

    id = Column(String, primary_key=True, default=gen_uuid)
    name = Column(String(255), nullable=False)
    slug = Column(String(255), unique=True, nullable=False, index=True)
    owner_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    is_active = Column(Boolean, default=True)
    settings = Column(JSON, default=dict)
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

    members = relationship("WorkspaceMember", back_populates="workspace", cascade="all, delete-orphan")
    agents = relationship("Agent", back_populates="workspace", cascade="all, delete-orphan")
    channels = relationship("Channel", back_populates="workspace", cascade="all, delete-orphan")
    contacts = relationship("Contact", back_populates="workspace", cascade="all, delete-orphan")
    conversations = relationship("Conversation", back_populates="workspace", cascade="all, delete-orphan")
    knowledge_sources = relationship("KnowledgeSource", back_populates="workspace", cascade="all, delete-orphan")


class WorkspaceMember(Base):
    __tablename__ = "workspace_members"

    id = Column(String, primary_key=True, default=gen_uuid)
    workspace_id = Column(String, ForeignKey("workspaces.id"), nullable=False, index=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    role = Column(String(50), default="member")  # owner, admin, member, viewer
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=utcnow)

    workspace = relationship("Workspace", back_populates="members")
