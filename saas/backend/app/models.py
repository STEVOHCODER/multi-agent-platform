"""Backward compatibility — import from modules instead."""
from app.modules.messaging import (
    EmailConnection, WhatsAppConnection, ForwardingRule, MessageLog, Usage,
)

__all__ = [
    "EmailConnection", "WhatsAppConnection", "ForwardingRule", "MessageLog", "Usage",
]
