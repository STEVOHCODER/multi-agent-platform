from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class AuditLogResponse(BaseModel):
    id: str
    workspace_id: str
    agent_id: Optional[str]
    action: str
    skill_name: Optional[str]
    parameters: dict
    result: dict
    confidence: Optional[float]
    actor_type: str
    actor_id: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class AgentRunResponse(BaseModel):
    id: str
    agent_id: str
    input_text: Optional[str]
    intent_detected: Optional[str]
    intent_confidence: Optional[float]
    skills_called: list
    output_text: Optional[str]
    status: str
    duration_ms: Optional[int]
    created_at: datetime

    class Config:
        from_attributes = True
