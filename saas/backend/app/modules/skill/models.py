import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Boolean, DateTime, Text, JSON, Integer
from app.modules.core.database import Base


def utcnow():
    return datetime.now(timezone.utc)


def gen_uuid():
    return str(uuid.uuid4())


class Skill(Base):
    """Global skill registry. Skills are reusable across agents and workspaces."""
    __tablename__ = "skills"

    id = Column(String, primary_key=True, default=gen_uuid)
    name = Column(String(255), unique=True, nullable=False, index=True)
    display_name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String(100), nullable=False, index=True)  # communication, finance, operations, email, memory
    version = Column(String(20), default="1.0.0")

    # Schema definitions
    input_schema = Column(JSON, default=dict)   # JSON Schema for inputs
    output_schema = Column(JSON, default=dict)  # JSON Schema for outputs
    config_schema = Column(JSON, default=dict)  # Configurable parameters

    # Permissions required
    required_permissions = Column(JSON, default=list)  # ["send_whatsapp", "read_email", "write_transaction"]

    # Behavior
    is_system = Column(Boolean, default=False)   # Built-in skills can't be deleted
    is_enabled = Column(Boolean, default=True)
    confidence_threshold = Column(Integer, default=70)  # Minimum confidence to execute (0-100)

    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)
