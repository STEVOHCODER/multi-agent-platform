from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class TransactionCreate(BaseModel):
    amount: float
    currency: str = "USD"
    recipient: str = ""
    sender: str = ""
    description: str = ""
    reference: str = ""


class TransactionResponse(BaseModel):
    id: str
    workspace_id: str
    status: str
    amount: float
    currency: str
    recipient: Optional[str]
    sender: Optional[str]
    description: Optional[str]
    reference: Optional[str]
    confidence: float
    ai_extracted: bool
    requested_at: Optional[datetime]
    settled_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


class TransactionEventResponse(BaseModel):
    id: str
    transaction_id: str
    from_status: Optional[str]
    to_status: str
    trigger: str
    reason: Optional[str]
    confidence: Optional[float]
    created_at: datetime

    class Config:
        from_attributes = True


class ReconciliationResponse(BaseModel):
    total_requested: float
    total_settled: float
    total_unsettled: float
    total_partially_settled: float
    total_cancelled: float
    settlement_rate: float
    transaction_count: int
    settled_count: int


class SettlementMatchResponse(BaseModel):
    transaction_id: str
    recipient: str
    amount: float
    confidence: float
    action: str
