import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Boolean, DateTime, Text, JSON, ForeignKey, Float, Integer
from sqlalchemy.orm import relationship
from app.modules.core.database import Base


def utcnow():
    return datetime.now(timezone.utc)


def gen_uuid():
    return str(uuid.uuid4())


# Valid state transitions
VALID_TRANSITIONS = {
    "REQUESTED":    ["UNSETTLED", "CANCELLED", "NEEDS_REVIEW"],
    "UNSETTLED":    ["PARTIALLY_SETTLED", "SETTLED", "CANCELLED", "DISPUTED", "NEEDS_REVIEW"],
    "PARTIALLY_SETTLED": ["SETTLED", "DISPUTED", "NEEDS_REVIEW"],
    "SETTLED":      ["DISPUTED"],
    "CANCELLED":    [],
    "DISPUTED":     ["NEEDS_REVIEW", "SETTLED"],
    "NEEDS_REVIEW": ["UNSETTLED", "SETTLED", "CANCELLED"],
}


class Transaction(Base):
    """A financial transaction tracked by the settlement agent."""
    __tablename__ = "transactions"

    id = Column(String, primary_key=True, default=gen_uuid)
    workspace_id = Column(String, ForeignKey("workspaces.id"), nullable=False, index=True)
    conversation_id = Column(String, ForeignKey("conversations.id"), nullable=True)

    # Transaction details
    status = Column(String(50), default="REQUESTED")  # State machine
    amount = Column(Float, nullable=False)
    currency = Column(String(10), default="USD")
    recipient = Column(String(255), nullable=True)
    sender = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)
    reference = Column(String(255), nullable=True)  # External reference

    # Dates
    requested_at = Column(DateTime, default=utcnow)
    settled_at = Column(DateTime, nullable=True)
    due_date = Column(DateTime, nullable=True)

    # AI metadata
    confidence = Column(Float, default=0.0)
    source_message_id = Column(String, ForeignKey("universal_messages.id"), nullable=True)
    ai_extracted = Column(Boolean, default=False)

    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

    events = relationship("TransactionEvent", back_populates="transaction", cascade="all, delete-orphan")


class TransactionEvent(Base):
    """Audit trail for every state change on a transaction."""
    __tablename__ = "transaction_events"

    id = Column(String, primary_key=True, default=gen_uuid)
    transaction_id = Column(String, ForeignKey("transactions.id"), nullable=False, index=True)
    workspace_id = Column(String, ForeignKey("workspaces.id"), nullable=False)

    from_status = Column(String(50), nullable=True)
    to_status = Column(String(50), nullable=False)
    trigger = Column(String(100), nullable=False)  # ai_detected, human_confirmed, system_reconciled
    reason = Column(Text, nullable=True)
    confidence = Column(Float, nullable=True)
    actor_id = Column(String, nullable=True)  # user_id or agent_id

    created_at = Column(DateTime, default=utcnow)

    transaction = relationship("Transaction", back_populates="events")
