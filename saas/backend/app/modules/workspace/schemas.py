from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class WorkspaceCreate(BaseModel):
    name: str


class WorkspaceResponse(BaseModel):
    id: str
    name: str
    slug: str
    owner_id: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class WorkspaceMemberResponse(BaseModel):
    id: str
    user_id: str
    role: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True
