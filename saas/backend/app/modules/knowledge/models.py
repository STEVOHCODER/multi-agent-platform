import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Boolean, DateTime, Text, JSON, ForeignKey
from sqlalchemy.orm import relationship
from app.modules.core.database import Base


def utcnow():
    return datetime.now(timezone.utc)


def gen_uuid():
    return str(uuid.uuid4())


class KnowledgeSource(Base):
    """Workspace-specific knowledge: FAQs, policies, products, documents."""
    __tablename__ = "knowledge_sources"

    id = Column(String, primary_key=True, default=gen_uuid)
    workspace_id = Column(String, ForeignKey("workspaces.id"), nullable=False, index=True)

    title = Column(String(500), nullable=False)
    content = Column(Text, nullable=False)
    category = Column(String(100), nullable=False, index=True)  # faq, policy, product, hours, general
    tags = Column(JSON, default=list)
    is_active = Column(Boolean, default=True)

    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

    workspace = relationship("Workspace", back_populates="knowledge_sources")
