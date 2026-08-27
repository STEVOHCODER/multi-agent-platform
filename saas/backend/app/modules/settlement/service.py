"""Settlement business logic — transaction state machine and reconciliation."""
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.modules.settlement.models import Transaction, TransactionEvent, VALID_TRANSITIONS


def create_transaction(
    db: Session,
    workspace_id: str,
    amount: float,
    currency: str = "USD",
    recipient: str = "",
    sender: str = "",
    description: str = "",
    reference: str = "",
    confidence: float = 0.0,
    source_message_id: str = None,
    conversation_id: str = None,
) -> Transaction:
    """Create a new transaction in REQUESTED state."""
    tx = Transaction(
        workspace_id=workspace_id,
        conversation_id=conversation_id,
        amount=amount,
        currency=currency,
        recipient=recipient,
        sender=sender,
        description=description,
        reference=reference,
        confidence=confidence,
        source_message_id=source_message_id,
        status="REQUESTED",
    )
    db.add(tx)
    db.flush()

    event = TransactionEvent(
        transaction_id=tx.id,
        workspace_id=workspace_id,
        from_status=None,
        to_status="REQUESTED",
        trigger="ai_detected",
        reason="Transaction created from message",
        confidence=confidence,
    )
    db.add(event)
    db.commit()
    db.refresh(tx)
    return tx


def transition_transaction(
    db: Session,
    transaction_id: str,
    new_status: str,
    trigger: str,
    reason: str = "",
    confidence: float = None,
    actor_id: str = None,
) -> Transaction:
    """Transition a transaction to a new status with validation."""
    tx = db.query(Transaction).filter(Transaction.id == transaction_id).first()
    if not tx:
        raise ValueError("Transaction not found")

    allowed = VALID_TRANSITIONS.get(tx.status, [])
    if new_status not in allowed:
        raise ValueError(f"Invalid transition: {tx.status} -> {new_status}")

    old_status = tx.status
    tx.status = new_status
    if new_status == "SETTLED":
        tx.settled_at = datetime.now(timezone.utc)

    event = TransactionEvent(
        transaction_id=tx.id,
        workspace_id=tx.workspace_id,
        from_status=old_status,
        to_status=new_status,
        trigger=trigger,
        reason=reason,
        confidence=confidence,
        actor_id=actor_id,
    )
    db.add(event)
    db.commit()
    db.refresh(tx)
    return tx


def match_and_settle(
    db: Session,
    workspace_id: str,
    text: str,
    confidence: float = 0.0,
) -> list[dict]:
    """Match a text message against unsettled transactions.
    Returns list of {transaction_id, confidence, action}."""
    unsettled = db.query(Transaction).filter(
        Transaction.workspace_id == workspace_id,
        Transaction.status.in_(["REQUESTED", "UNSETTLED", "PARTIALLY_SETTLED"]),
    ).all()

    matches = []
    text_lower = text.lower()

    for tx in unsettled:
        score = 0.0
        # Match by recipient name
        if tx.recipient and tx.recipient.lower() in text_lower:
            score += 0.4
        # Match by amount
        if str(int(tx.amount)) in text or f"{tx.amount:.2f}" in text:
            score += 0.4
        # Match by reference
        if tx.reference and tx.reference.lower() in text_lower:
            score += 0.2

        if score > 0.3:
            matches.append({
                "transaction_id": tx.id,
                "recipient": tx.recipient,
                "amount": tx.amount,
                "confidence": min(score + confidence * 0.2, 1.0),
                "action": "settle" if score > 0.7 else "needs_review",
            })

    return sorted(matches, key=lambda m: m["confidence"], reverse=True)


def reconcile_date_range(
    db: Session,
    workspace_id: str,
    start_date: datetime,
    end_date: datetime,
) -> dict:
    """Reconcile all transactions in a date range. Deterministic — no AI."""
    txs = db.query(Transaction).filter(
        Transaction.workspace_id == workspace_id,
        Transaction.created_at >= start_date,
        Transaction.created_at <= end_date,
    ).all()

    total_requested = sum(tx.amount for tx in txs if tx.status == "REQUESTED")
    total_settled = sum(tx.amount for tx in txs if tx.status == "SETTLED")
    total_unsettled = sum(tx.amount for tx in txs if tx.status in ("REQUESTED", "UNSETTLED"))
    total_partial = sum(tx.amount for tx in txs if tx.status == "PARTIALLY_SETTLED")
    total_cancelled = sum(tx.amount for tx in txs if tx.status == "CANCELLED")

    count = len(txs)
    settled_count = sum(1 for tx in txs if tx.status == "SETTLED")
    rate = (settled_count / count * 100) if count > 0 else 0.0

    return {
        "total_requested": total_requested,
        "total_settled": total_settled,
        "total_unsettled": total_unsettled,
        "total_partially_settled": total_partial,
        "total_cancelled": total_cancelled,
        "settlement_rate": round(rate, 2),
        "transaction_count": count,
        "settled_count": settled_count,
    }


def find_unsettled(db: Session, workspace_id: str) -> dict:
    """Find all unsettled transactions."""
    txs = db.query(Transaction).filter(
        Transaction.workspace_id == workspace_id,
        Transaction.status.in_(["REQUESTED", "UNSETTLED", "PARTIALLY_SETTLED"]),
    ).order_by(Transaction.created_at.desc()).all()

    return {
        "transactions": [
            {
                "id": tx.id,
                "amount": tx.amount,
                "currency": tx.currency,
                "recipient": tx.recipient,
                "status": tx.status,
                "requested_at": tx.requested_at.isoformat() if tx.requested_at else None,
            }
            for tx in txs
        ],
        "total_amount": sum(tx.amount for tx in txs),
        "count": len(txs),
    }


def generate_daily_report(db: Session, workspace_id: str, date: datetime = None) -> dict:
    """Generate a daily settlement report."""
    if date is None:
        date = datetime.now(timezone.utc)
    start = date.replace(hour=0, minute=0, second=0, microsecond=0)
    end = start + timedelta(days=1)

    reconciliation = reconcile_date_range(db, workspace_id, start, end)

    unsettled = find_unsettled(db, workspace_id)

    return {
        "date": start.strftime("%Y-%m-%d"),
        "summary": reconciliation,
        "unsettled": unsettled,
        "report_text": (
            f"Daily Report — {start.strftime('%Y-%m-%d')}\n"
            f"Total Requested: ${reconciliation['total_requested']:,.2f}\n"
            f"Total Settled: ${reconciliation['total_settled']:,.2f}\n"
            f"Total Unsettled: ${reconciliation['total_unsettled']:,.2f}\n"
            f"Settlement Rate: {reconciliation['settlement_rate']}%\n"
            f"Transactions: {reconciliation['transaction_count']}"
        ),
    }
