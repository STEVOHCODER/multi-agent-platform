from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta, timezone

from app.modules.core.database import get_db
from app.modules.auth.models import User
from app.modules.auth.service import get_current_user
from app.modules.billing.models import Subscription
from app.modules.messaging.models import (
    EmailConnection, WhatsAppConnection, ForwardingRule, MessageLog, Usage,
)
from app.modules.messaging.schemas import (
    EmailConnect, EmailConnectionResponse,
    WhatsAppConnect, WhatsAppResponse,
    RuleCreate, RuleUpdate, RuleResponse,
    MessageLogResponse, DashboardResponse, UsageResponse,
)

router = APIRouter(prefix="/api/messaging", tags=["messaging"])


# ── Email Connections ──────────────────────────────────────────────
@router.get("/email/connections", response_model=list[EmailConnectionResponse])
def list_email_connections(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    conns = db.query(EmailConnection).filter(EmailConnection.user_id == user.id).all()
    return [EmailConnectionResponse.model_validate(c) for c in conns]


@router.post("/email/connect", response_model=EmailConnectionResponse)
def connect_email(
    data: EmailConnect,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    existing = (
        db.query(EmailConnection)
        .filter(EmailConnection.user_id == user.id, EmailConnection.email_address == data.email_address.lower())
        .first()
    )
    if existing:
        raise HTTPException(status_code=400, detail="Email already connected")

    conn = EmailConnection(
        user_id=user.id,
        provider=data.provider,
        email_address=data.email_address.lower(),
        encrypted_token=data.password,
        imap_host=data.imap_host,
        imap_port=data.imap_port,
    )
    db.add(conn)
    db.commit()
    db.refresh(conn)
    return EmailConnectionResponse.model_validate(conn)


@router.delete("/email/connections/{connection_id}")
def disconnect_email(
    connection_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    conn = (
        db.query(EmailConnection)
        .filter(EmailConnection.id == connection_id, EmailConnection.user_id == user.id)
        .first()
    )
    if not conn:
        raise HTTPException(status_code=404, detail="Connection not found")
    db.delete(conn)
    db.commit()
    return {"ok": True}


# ── WhatsApp ───────────────────────────────────────────────────────
@router.get("/whatsapp/connection", response_model=WhatsAppResponse | None)
def get_whatsapp_connection(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    conn = db.query(WhatsAppConnection).filter(WhatsAppConnection.user_id == user.id).first()
    if not conn:
        return None
    return WhatsAppResponse.model_validate(conn)


@router.post("/whatsapp/connect", response_model=WhatsAppResponse)
def connect_whatsapp(
    data: WhatsAppConnect,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    existing = db.query(WhatsAppConnection).filter(WhatsAppConnection.user_id == user.id).first()
    if existing:
        raise HTTPException(status_code=400, detail="WhatsApp already connected. Disconnect first.")

    conn = WhatsAppConnection(
        user_id=user.id,
        phone_number=data.phone_number,
        meta_phone_number_id=data.meta_phone_number_id,
        meta_access_token=data.meta_access_token,
    )
    db.add(conn)
    db.commit()
    db.refresh(conn)
    return WhatsAppResponse.model_validate(conn)


@router.delete("/whatsapp/connection")
def disconnect_whatsapp(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    conn = db.query(WhatsAppConnection).filter(WhatsAppConnection.user_id == user.id).first()
    if not conn:
        raise HTTPException(status_code=404, detail="No WhatsApp connection")
    db.delete(conn)
    db.commit()
    return {"ok": True}


@router.post("/whatsapp/test")
def send_test_message(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    conn = db.query(WhatsAppConnection).filter(WhatsAppConnection.user_id == user.id).first()
    if not conn:
        raise HTTPException(status_code=404, detail="No WhatsApp connection")

    import requests as req
    url = f"https://graph.facebook.com/v21.0/{conn.meta_phone_number_id}/messages"
    payload = {
        "messaging_product": "whatsapp",
        "to": conn.phone_number,
        "type": "text",
        "text": {"body": "MailPilot test message — your WhatsApp connection is working!"},
    }
    resp = req.post(url, headers={"Authorization": f"Bearer {conn.meta_access_token}", "Content-Type": "application/json"}, json=payload, timeout=20)
    if resp.status_code >= 400:
        raise HTTPException(status_code=400, detail=f"Meta API error: {resp.text[:300]}")
    return {"ok": True, "message_id": resp.json().get("messages", [{}])[0].get("id")}


# ── Forwarding Rules ───────────────────────────────────────────────
@router.get("/rules", response_model=list[RuleResponse])
def list_rules(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    rules = (
        db.query(ForwardingRule)
        .filter(ForwardingRule.user_id == user.id)
        .order_by(ForwardingRule.priority.desc())
        .all()
    )
    return [RuleResponse.model_validate(r) for r in rules]


@router.post("/rules", response_model=RuleResponse)
def create_rule(
    data: RuleCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    rule = ForwardingRule(user_id=user.id, **data.model_dump())
    db.add(rule)
    db.commit()
    db.refresh(rule)
    return RuleResponse.model_validate(rule)


@router.put("/rules/{rule_id}", response_model=RuleResponse)
def update_rule(
    rule_id: str,
    data: RuleUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    rule = db.query(ForwardingRule).filter(ForwardingRule.id == rule_id, ForwardingRule.user_id == user.id).first()
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(rule, k, v)
    db.commit()
    db.refresh(rule)
    return RuleResponse.model_validate(rule)


@router.delete("/rules/{rule_id}")
def delete_rule(
    rule_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    rule = db.query(ForwardingRule).filter(ForwardingRule.id == rule_id, ForwardingRule.user_id == user.id).first()
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    db.delete(rule)
    db.commit()
    return {"ok": True}


# ── Dashboard ──────────────────────────────────────────────────────
@router.get("/dashboard", response_model=DashboardResponse)
def get_dashboard(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    month_start = today_start.replace(day=1)

    email_count = db.query(EmailConnection).filter(EmailConnection.user_id == user.id, EmailConnection.is_active == True).count()
    whatsapp = db.query(WhatsAppConnection).filter(WhatsAppConnection.user_id == user.id).first()
    sub = db.query(Subscription).filter(Subscription.user_id == user.id).first()

    today_count = (
        db.query(func.count(MessageLog.id))
        .filter(MessageLog.user_id == user.id, MessageLog.created_at >= today_start)
        .scalar()
    )
    month_count = (
        db.query(func.count(MessageLog.id))
        .filter(MessageLog.user_id == user.id, MessageLog.created_at >= month_start)
        .scalar()
    )

    recent = (
        db.query(MessageLog)
        .filter(MessageLog.user_id == user.id)
        .order_by(MessageLog.created_at.desc())
        .limit(20)
        .all()
    )

    return DashboardResponse(
        status="active" if whatsapp and whatsapp.is_active else "inactive",
        email_connections=email_count,
        whatsapp_connected=whatsapp is not None and whatsapp.is_active,
        messages_today=today_count,
        messages_this_month=month_count,
        plan=sub.plan if sub else "free",
        recent_messages=[MessageLogResponse.model_validate(m) for m in recent],
    )


@router.get("/messages", response_model=list[MessageLogResponse])
def list_messages(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    limit: int = 50,
):
    msgs = (
        db.query(MessageLog)
        .filter(MessageLog.user_id == user.id)
        .order_by(MessageLog.created_at.desc())
        .limit(limit)
        .all()
    )
    return [MessageLogResponse.model_validate(m) for m in msgs]


@router.get("/usage", response_model=UsageResponse)
def get_usage(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    usage = db.query(Usage).filter(Usage.user_id == user.id).first()
    if not usage:
        return UsageResponse(
            emails_received=0, emails_processed=0,
            messages_forwarded=0, messages_failed=0,
            period_start=None, period_end=None,
        )
    return UsageResponse.model_validate(usage)


# ── Admin ──────────────────────────────────────────────────────────
@router.get("/admin/stats")
def get_admin_stats(admin: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not admin.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    return {
        "total_users": db.query(func.count(User.id)).scalar(),
        "active_users": db.query(func.count(User.id)).filter(User.is_active == True).scalar(),
        "total_email_connections": db.query(func.count(EmailConnection.id)).filter(EmailConnection.is_active == True).scalar(),
        "total_whatsapp_connections": db.query(func.count(WhatsAppConnection.id)).filter(WhatsAppConnection.is_active == True).scalar(),
        "total_messages": db.query(func.count(MessageLog.id)).scalar(),
        "messages_forwarded": db.query(func.count(MessageLog.id)).filter(MessageLog.forwarded == True).scalar(),
        "messages_failed": db.query(func.count(MessageLog.id)).filter(MessageLog.delivery_status == "failed").scalar(),
        "plans": dict(db.query(Subscription.plan, func.count(Subscription.id)).group_by(Subscription.plan).all()),
    }


@router.get("/admin/users")
def list_admin_users(admin: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not admin.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    users = db.query(User).order_by(User.created_at.desc()).all()
    result = []
    for u in users:
        sub = db.query(Subscription).filter(Subscription.user_id == u.id).first()
        usage = db.query(Usage).filter(Usage.user_id == u.id).first()
        result.append({
            "id": u.id,
            "email": u.email,
            "name": u.name,
            "is_active": u.is_active,
            "plan": sub.plan if sub else "free",
            "messages_forwarded": usage.messages_forwarded if usage else 0,
            "created_at": u.created_at.isoformat() if u.created_at else None,
        })
    return result


@router.post("/admin/users/{user_id}/toggle")
def toggle_user(user_id: str, admin: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not admin.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return {"error": "not found"}
    user.is_active = not user.is_active
    db.commit()
    return {"ok": True, "is_active": user.is_active}
