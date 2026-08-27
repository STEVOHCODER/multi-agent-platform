import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Boolean, DateTime
from app.modules.core.database import Base


def utcnow():
    return datetime.now(timezone.utc)


def gen_uuid():
    return str(uuid.uuid4())


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=gen_uuid)
    email = Column(String(255), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False, default="")
    password_hash = Column(String(255), nullable=False)
    timezone = Column(String(50), default="UTC")
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)
