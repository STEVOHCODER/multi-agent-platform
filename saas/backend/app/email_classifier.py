"""Backward compatibility — import from modules instead."""
from app.modules.messaging import classify_email

__all__ = ["classify_email"]
