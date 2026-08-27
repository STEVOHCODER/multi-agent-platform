"""Backward compatibility — import from modules instead."""
from app.modules.auth.schemas import UserRegister, UserLogin, UserResponse, TokenResponse
from app.modules.messaging.schemas import (
    EmailConnect, EmailConnectionResponse,
    WhatsAppConnect, WhatsAppResponse,
    RuleCreate, RuleUpdate, RuleResponse,
    MessageLogResponse, DashboardResponse, UsageResponse,
)
from app.modules.billing.schemas import SubscriptionResponse

__all__ = [
    "UserRegister", "UserLogin", "UserResponse", "TokenResponse",
    "EmailConnect", "EmailConnectionResponse",
    "WhatsAppConnect", "WhatsAppResponse",
    "RuleCreate", "RuleUpdate", "RuleResponse",
    "MessageLogResponse", "DashboardResponse", "UsageResponse",
    "SubscriptionResponse",
]
