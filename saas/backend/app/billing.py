"""Backward compatibility — import from modules instead."""
from app.modules.billing import (
    Subscription, PLANS, create_checkout_session, create_portal_session, handle_webhook,
)

__all__ = [
    "Subscription", "PLANS", "create_checkout_session", "create_portal_session", "handle_webhook",
]
