import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.modules.core.database import Base


def utcnow():
    return datetime.now(timezone.utc)


def gen_uuid():
    return str(uuid.uuid4())


class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(String, primary_key=True, default=gen_uuid)
    user_id = Column(String, ForeignKey("users.id"), unique=True, nullable=False)
    plan = Column(String(50), default="free")
    status = Column(String(50), default="active")
    stripe_subscription_id = Column(String(255), nullable=True)
    stripe_customer_id = Column(String(255), nullable=True)
    current_period_start = Column(DateTime, nullable=True)
    current_period_end = Column(DateTime, nullable=True)
    cancel_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=utcnow)
