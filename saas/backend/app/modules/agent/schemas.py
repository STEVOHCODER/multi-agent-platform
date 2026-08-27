from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class AgentCreate(BaseModel):
    name: str
    description: str = ""
    model: str = "gpt-4o-mini"
    system_instructions: str = ""
    skills: list[str] = []
    channels: list[str] = []
    response_mode: str = "off"
    auto_reply: bool = False
    memory_enabled: bool = True
    confidence_threshold: int = 70
    simulation_mode: bool = False


class AgentUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    model: Optional[str] = None
    system_instructions: Optional[str] = None
    response_mode: Optional[str] = None
    auto_reply: Optional[bool] = None
    memory_enabled: Optional[bool] = None
    confidence_threshold: Optional[int] = None
    simulation_mode: Optional[bool] = None
    status: Optional[str] = None


class AgentResponse(BaseModel):
    id: str
    workspace_id: str
    name: str
    description: Optional[str]
    model: str
    response_mode: str
    auto_reply: bool
    memory_enabled: bool
    channels: list
    status: str
    simulation_mode: bool
    confidence_threshold: int
    created_at: datetime

    class Config:
        from_attributes = True


class AgentSkillResponse(BaseModel):
    id: str
    skill_name: str
    is_enabled: bool
    config: dict

    class Config:
        from_attributes = True


class AgentTemplateResponse(BaseModel):
    id: str
    name: str
    description: str
    model: str
    skills: list[str]
    channels: list[str]
    response_mode: str
