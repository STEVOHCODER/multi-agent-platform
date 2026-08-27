"""Backward compatibility — import from modules instead."""
from app.modules.messaging import send_whatsapp_message

__all__ = ["send_whatsapp_message"]
