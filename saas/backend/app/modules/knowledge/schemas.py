from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class KnowledgeCreate(BaseModel):
    title: str
    content: str
    category: str = "general"
    tags: list[str] = []


class KnowledgeUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    category: Optional[str] = None
    tags: Optional[list[str]] = None
    is_active: Optional[bool] = None


class KnowledgeResponse(BaseModel):
    id: str
    workspace_id: str
    title: str
    content: str
    category: str
    tags: list
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True
