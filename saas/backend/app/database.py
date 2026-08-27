"""Backward compatibility — import from modules instead."""
from app.modules.core import Base, get_db, init_db

__all__ = ["Base", "get_db", "init_db"]
