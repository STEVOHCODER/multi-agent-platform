from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timezone, timedelta

from app.modules.core.database import get_db
from app.modules.auth.models import User
from app.modules.auth.service import get_current_user
from app.modules.workspace.models import WorkspaceMember
from app.modules.settlement.models import Transaction, TransactionEvent
from app.modules.settlement.service import (
    create_transaction, transition_transaction, match_and_settle,
    reconcile_date_range, find_unsettled, generate_daily_report,
)
from app.modules.settlement.schemas import (
    TransactionCreate, TransactionResponse, TransactionEventResponse,
    ReconciliationResponse, SettlementMatchResponse,
)

router = APIRouter(prefix="/api/settlement", tags=["settlement"])


def _check_workspace(workspace_id: str, user: User, db: Session):
    member = db.query(WorkspaceMember).filter(
        WorkspaceMember.workspace_id == workspace_id,
        WorkspaceMember.user_id == user.id,
        WorkspaceMember.is_active == True,
    ).first()
    if not member:
        raise HTTPException(status_code=403, detail="Not a member of this workspace")
    return member


@router.post("/workspace/{workspace_id}/transactions", response_model=TransactionResponse)
def create_tx(
    workspace_id: str,
    data: TransactionCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _check_workspace(workspace_id, user, db)
    tx = create_transaction(db, workspace_id, **data.model_dump())
    return TransactionResponse.model_validate(tx)


@router.get("/workspace/{workspace_id}/transactions", response_model=list[TransactionResponse])
def list_transactions(
    workspace_id: str,
    status: str = None,
    limit: int = 50,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _check_workspace(workspace_id, user, db)
    q = db.query(Transaction).filter(Transaction.workspace_id == workspace_id)
    if status:
        q = q.filter(Transaction.status == status)
    txs = q.order_by(Transaction.created_at.desc()).limit(limit).all()
    return [TransactionResponse.model_validate(tx) for tx in txs]


@router.get("/workspace/{workspace_id}/transactions/{tx_id}", response_model=TransactionResponse)
def get_transaction(
    workspace_id: str,
    tx_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _check_workspace(workspace_id, user, db)
    tx = db.query(Transaction).filter(Transaction.id == tx_id, Transaction.workspace_id == workspace_id).first()
    if not tx:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return TransactionResponse.model_validate(tx)


@router.post("/workspace/{workspace_id}/transactions/{tx_id}/transition")
def transition_tx(
    workspace_id: str,
    tx_id: str,
    new_status: str,
    reason: str = "",
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _check_workspace(workspace_id, user, db)
    try:
        tx = transition_transaction(db, tx_id, new_status, trigger="human_confirmed", reason=reason, actor_id=user.id)
        return TransactionResponse.model_validate(tx)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/workspace/{workspace_id}/match", response_model=list[SettlementMatchResponse])
def match_settlement(
    workspace_id: str,
    text: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _check_workspace(workspace_id, user, db)
    matches = match_and_settle(db, workspace_id, text)
    return [SettlementMatchResponse(**m) for m in matches]


@router.get("/workspace/{workspace_id}/unsettled")
def get_unsettled(
    workspace_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _check_workspace(workspace_id, user, db)
    return find_unsettled(db, workspace_id)


@router.get("/workspace/{workspace_id}/reconcile", response_model=ReconciliationResponse)
def reconcile(
    workspace_id: str,
    days: int = 1,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _check_workspace(workspace_id, user, db)
    now = datetime.now(timezone.utc)
    start = now - timedelta(days=days)
    result = reconcile_date_range(db, workspace_id, start, now)
    return ReconciliationResponse(**result)


@router.get("/workspace/{workspace_id}/report")
def daily_report(
    workspace_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _check_workspace(workspace_id, user, db)
    return generate_daily_report(db, workspace_id)
