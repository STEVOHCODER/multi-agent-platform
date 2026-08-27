"""Backward compatibility — import from modules instead."""
from app.modules.auth import (
    User, hash_password, verify_password, create_access_token,
    decode_token, get_current_user, require_admin,
)

__all__ = [
    "User", "hash_password", "verify_password", "create_access_token",
    "decode_token", "get_current_user", "require_admin",
]
