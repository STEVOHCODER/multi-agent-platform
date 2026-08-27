import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Boolean, DateTime, Text, JSON, ForeignKey, Float, Integer
from sqlalchemy.orm import relationship
from app.modules.core.database import Base


def utcnow():
    return datetime.now(timezone.utc)


def gen_uuid():
    return str(uuid.uuid4())


class AuditLog(Base):
    """Audit trail for agent actions, tool calls, and human corrections."""
    __tablename__ = "audit_logs"

    id = Column(String, primary_key=True, default=gen_uuid)
    workspace_id = Column(String, ForeignKey("workspaces.id"), nullable=False, index=True)
    agent_id = Column(String, ForeignKey("agents.id"), nullable=True, index=True)
    conversation_id = Column(String, ForeignKey("conversations.id"), nullable=True)

    action = Column(String(255), nullable=False)  # skill_called, message_sent, transaction_created, etc.
    skill_name = Column(String(255), nullable=True)
    parameters = Column(JSON, default=dict)
    result = Column(JSON, default=dict)
    confidence = Column(Float, nullable=True)

    # Safety
    approved = Column(Boolean, default=True)
    rejected_reason = Column(String(500), nullable=True)

    # Actor
    actor_type = Column(String(50), nullable=False)  # agent, human, system
    actor_id = Column(String(255), nullable=True)

    created_at = Column(DateTime, default=utcnow)


class AgentRun(Base):
    """Records each time an agent processes a message."""
    __tablename__ = "agent_runs"

    id = Column(String, primary_key=True, default=gen_uuid)
    workspace_id = Column(String, ForeignKey("workspaces.id"), nullable=False, index=True)
    agent_id = Column(String, ForeignKey("agents.id"), nullable=False, index=True)
    conversation_id = Column(String, ForeignKey("conversations.id"), nullable=True)
    message_id = Column(String, ForeignKey("universal_messages.id"), nullable=True)

    # Execution
    input_text = Column(Text, nullable=True)
    intent_detected = Column(String(255), nullable=True)
    intent_confidence = Column(Float, nullable=True)
    skills_called = Column(JSON, default=list)
    output_text = Column(Text, nullable=True)

    # Status
    status = Column(String(50), default="completed")  # completed, failed, escalated, needs_review
    error = Column(Text, nullable=True)
    duration_ms = Column(Integer, nullable=True)

    created_at = Column(DateTime, default=utcnow)

    agent = relationship("Agent", back_populates="runs")
    tool_calls = relationship("ToolCall", back_populates="agent_run", cascade="all, delete-orphan")


class ToolCall(Base):
    """Individual skill/tool invocation within an agent run."""
    __tablename__ = "tool_calls"

    id = Column(String, primary_key=True, default=gen_uuid)
    agent_run_id = Column(String, ForeignKey("agent_runs.id"), nullable=False, index=True)

    skill_name = Column(String(255), nullable=False)
    input_params = Column(JSON, default=dict)
    output_result = Column(JSON, default=dict)
    confidence = Column(Float, nullable=True)
    status = Column(String(50), default="success")  # success, failed, skipped
    duration_ms = Column(Integer, nullable=True)

    created_at = Column(DateTime, default=utcnow)

    agent_run = relationship("AgentRun", back_populates="tool_calls")
