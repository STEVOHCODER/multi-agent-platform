"""Modular SaaS backend — import individual modules as needed."""
from app.modules.core import Base, get_db, init_db, Settings, settings
from app.modules.auth import User, auth_router
from app.modules.billing import Subscription, billing_router
from app.modules.messaging import (
    EmailConnection, WhatsAppConnection, ForwardingRule, MessageLog, Usage,
    messaging_router,
)
from app.modules.worker import start_worker_loop, poll_all_tenants

__all__ = [
    # Core
    "Base", "get_db", "init_db", "Settings", "settings",
    # Auth
    "User", "auth_router",
    # Billing
    "Subscription", "billing_router",
    # Messaging
    "EmailConnection", "WhatsAppConnection", "ForwardingRule", "MessageLog", "Usage",
    "messaging_router",
    # Worker
    "start_worker_loop", "poll_all_tenants",
]
