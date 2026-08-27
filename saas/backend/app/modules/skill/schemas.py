from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class SkillResponse(BaseModel):
    id: str
    name: str
    display_name: str
    description: Optional[str]
    category: str
    version: str
    is_enabled: bool
    confidence_threshold: int

    class Config:
        from_attributes = True


class SkillDefinitionResponse(BaseModel):
    name: str
    display_name: str
    description: str
    category: str
    input_schema: dict
    output_schema: dict
    required_permissions: list[str]
    confidence_threshold: int
