import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Boolean, DateTime, Text, JSON, ForeignKey, Integer
from sqlalchemy.orm import relationship
from app.modules.core.database import Base


def utcnow():
    return datetime.now(timezone.utc)


def gen_uuid():
    return str(uuid.uuid4())


class Agent(Base):
    """Configurable AI agent owned by a workspace."""
    __tablename__ = "agents"

    id = Column(String, primary_key=True, default=gen_uuid)
    workspace_id = Column(String, ForeignKey("workspaces.id"), nullable=False, index=True)
    template_id = Column(String, nullable=True)  # Which template this was created from (if any)

    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    model = Column(String(100), default="gpt-4o-mini")  # AI model identifier
    system_instructions = Column(Text, nullable=True)

    # Response policy
    response_mode = Column(String(50), default="off")  # off, suggest, auto, auto_escalation
    confidence_threshold = Column(Integer, default=70)

    # Behavior
    memory_enabled = Column(Boolean, default=True)
    auto_reply = Column(Boolean, default=False)
    channels = Column(JSON, default=list)  # ["whatsapp", "email"]  — channels this agent listens on
    status = Column(String(50), default="active")  # active, paused, draft

    # Simulation
    simulation_mode = Column(Boolean, default=False)

    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

    workspace = relationship("Workspace", back_populates="agents")
    skills = relationship("AgentSkillLink", back_populates="agent", cascade="all, delete-orphan")
    runs = relationship("AgentRun", back_populates="agent")


class AgentSkillLink(Base):
    """Many-to-many: which skills an agent has."""
    __tablename__ = "agent_skills"

    id = Column(String, primary_key=True, default=gen_uuid)
    agent_id = Column(String, ForeignKey("agents.id"), nullable=False, index=True)
    skill_id = Column(String, ForeignKey("skills.id"), nullable=False, index=True)
    config = Column(JSON, default=dict)  # Skill-specific config overrides
    is_enabled = Column(Boolean, default=True)
    created_at = Column(DateTime, default=utcnow)

    agent = relationship("Agent", back_populates="skills")
    skill = relationship("Skill")
