from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class SubscriptionResponse(BaseModel):
    plan: str
    status: str
    current_period_end: Optional[datetime]
    emails_limit: int
    emails_used: int

    class Config:
        from_attributes = True
