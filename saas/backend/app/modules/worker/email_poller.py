"""Per-tenant email polling worker."""
import logging
import asyncio
import imaplib
import email
from email.header import decode_header
from datetime import datetime, timezone
from typing import List
import hashlib
import json

from sqlalchemy.orm import Session
from app.modules.core.database import get_db
from app.modules.auth.models import User
from app.modules.messaging.models import (
    EmailConnection, WhatsAppConnection,
    ForwardingRule, MessageLog, Usage,
)
from app.modules.messaging.whatsapp_sender import send_whatsapp_message
from app.modules.messaging.email_classifier import classify_email

logger = logging.getLogger("mailpilot.worker")


async def poll_all_tenants():
    """Poll all active tenants' email inboxes."""
    db = next(get_db())
    try:
        active_connections = (
            db.query(EmailConnection)
            .filter(EmailConnection.is_active == True)
            .all()
        )
        logger.info(f"Polling {len(active_connections)} email connections")
        for conn in active_connections:
            try:
                await poll_connection(db, conn)
            except Exception as e:
                logger.error(f"Error polling connection {conn.id}: {e}")
                conn.last_error = str(e)[:500]
                db.commit()
        db.commit()
    finally:
        db.close()


async def poll_connection(db: Session, conn: EmailConnection):
    """Poll a single email connection and forward new messages."""
    if conn.provider == "gmail" and conn.encrypted_token:
        messages = await fetch_gmail(conn)
    else:
        messages = await fetch_imap(conn)

    if not messages:
        return

    user = db.query(User).filter(User.id == conn.user_id).first()
    if not user:
        return

    rules = (
        db.query(ForwardingRule)
        .filter(ForwardingRule.user_id == user.id, ForwardingRule.is_active == True)
        .all()
    )

    whatsapp_conn = (
        db.query(WhatsAppConnection)
        .filter(WhatsAppConnection.user_id == user.id, WhatsAppConnection.is_active == True)
        .first()
    )

    if not whatsapp_conn:
        logger.debug(f"No WhatsApp connection for user {user.id}")
        return

    plan = getattr(user, "plan", None) or "free"
    daily_limit = {"free": 25, "pro": 250, "enterprise": -1}.get(plan, 25)
    today_count = (
        db.query(MessageLog)
        .filter(
            MessageLog.user_id == user.id,
            MessageLog.created_at >= datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0),
            MessageLog.delivery_status == "sent",
        )
        .count()
    )

    for msg in messages:
        msg_hash = hashlib.sha256(
            f"{conn.id}:{msg.get('subject', '')}{msg.get('from', '')}{msg.get('date', '')}".encode()
        ).hexdigest()

        exists = db.query(MessageLog).filter(
            MessageLog.user_id == user.id,
            MessageLog.email_message_id == msg_hash,
        ).first()
        if exists:
            continue

        matched_rules = match_rules(msg, rules)
        if not matched_rules and rules:
            logger.debug(f"No rule match for: {msg.get('subject', '')[:50]}")
            continue

        importance = await classify_email(msg)

        if daily_limit != -1 and today_count >= daily_limit:
            logger.warning(f"User {user.id} hit daily limit ({daily_limit})")
            log = MessageLog(
                user_id=user.id,
                email_connection_id=conn.id,
                email_subject=msg.get("subject", "")[:500],
                email_sender=msg.get("from", "")[:250],
                classification_score=importance,
                delivery_status="skipped",
                delivery_error="Daily limit reached",
                email_message_id=msg_hash,
            )
            db.add(log)
            db.commit()
            break

        result = await send_whatsapp_message(
            phone_number=whatsapp_conn.phone_number,
            meta_phone_number_id=whatsapp_conn.meta_phone_number_id,
            meta_access_token=whatsapp_conn.meta_access_token,
            subject=msg.get("subject", ""),
            sender=msg.get("from", ""),
            body=msg.get("body", "")[:500],
            importance=importance,
        )

        log = MessageLog(
            user_id=user.id,
            email_connection_id=conn.id,
            whatsapp_connection_id=whatsapp_conn.id,
            email_subject=msg.get("subject", "")[:500],
            email_sender=msg.get("from", "")[:250],
            classification_score=importance,
            delivery_status="sent" if result.get("ok") else "failed",
            whatsapp_message_id=result.get("message_id", ""),
            delivery_error=result.get("error", ""),
            email_message_id=msg_hash,
        )
        db.add(log)

        usage = db.query(Usage).filter(Usage.user_id == user.id).first()
        if usage:
            usage.messages_forwarded += 1
        else:
            db.add(Usage(user_id=user.id, messages_forwarded=1))

        today_count += 1
        logger.info(f"Forwarded: {msg.get('subject', '')[:50]} -> {whatsapp_conn.phone_number}")

    db.commit()


def match_rules(msg: dict, rules: List[ForwardingRule]) -> List[ForwardingRule]:
    """Check if a message matches any forwarding rules."""
    matched = []
    for rule in rules:
        if not rule.is_active:
            continue
        if rule.sender_emails:
            sender = msg.get("from", "").lower()
            if not any(e.lower() in sender for e in rule.sender_emails):
                continue
        if rule.subject_contains:
            subject = msg.get("subject", "").lower()
            if not any(k.lower() in subject for k in rule.subject_contains):
                continue
        if rule.body_contains:
            body = msg.get("body", "").lower()
            if not any(k.lower() in body for k in rule.body_contains):
                continue
        if rule.min_importance_score and rule.min_importance_score > 0:
            continue
        matched.append(rule)
    return matched if matched else [rules[0]] if rules else []


async def fetch_imap(conn: EmailConnection) -> List[dict]:
    """Fetch messages via IMAP."""
    messages = []
    try:
        import socks
        socks.set_default_proxy(socks.SOCKS5, "192.168.43.1", 1080)
        socks.wrapmodule(imaplib)
    except ImportError:
        pass

    try:
        imap = imaplib.IMAP4_SSL(conn.imap_host or "imap.gmail.com", conn.imap_port or 993, timeout=15)
        imap.login(conn.email_address, conn.encrypted_token)
        imap.select("INBOX")
        _, data = imap.search(None, "UNSEEN")
        for num in data[0].split()[:5]:
            _, msg_data = imap.fetch(num, "(RFC822)")
            raw = msg_data[0][1]
            email_msg = email.message_from_bytes(raw)
            subject = ""
            for part, enc in decode_header(email_msg.get("Subject", "")):
                if isinstance(part, bytes):
                    subject += part.decode(enc or "utf-8", errors="replace")
                else:
                    subject += part
            body = ""
            if email_msg.is_multipart():
                for part in email_msg.walk():
                    if part.get_content_type() == "text/plain":
                        body = part.get_payload(decode=True).decode("utf-8", errors="replace")[:2000]
                        break
            else:
                body = email_msg.get_payload(decode=True).decode("utf-8", errors="replace")[:2000]
            messages.append({
                "from": email.utils.parseaddr(email_msg.get("From", ""))[1],
                "to": email.utils.parseaddr(email_msg.get("To", ""))[1],
                "subject": subject,
                "body": body,
                "date": email_msg.get("Date", ""),
            })
        imap.logout()
    except Exception as e:
        logger.error(f"IMAP fetch error for {conn.email_address}: {e}")
    return messages


async def fetch_gmail(conn: EmailConnection) -> List[dict]:
    """Fetch messages via Gmail REST API."""
    import aiohttp
    messages = []
    try:
        url = "https://www.googleapis.com/gmail/v1/users/me/messages"
        headers = {"Authorization": f"Bearer {conn.encrypted_token}"}
        params = {"q": "is:unread in:inbox", "maxResults": 5}
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, params=params, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                if resp.status != 200:
                    return []
                data = await resp.json()
                for m in data.get("messages", []):
                    msg_url = f"https://www.googleapis.com/gmail/v1/users/me/messages/{m['id']}"
                    async with session.get(msg_url, headers=headers, params={"format": "full"}, timeout=aiohttp.ClientTimeout(total=10)) as msg_resp:
                        if msg_resp.status != 200:
                            continue
                        msg_data = await msg_resp.json()
                        headers_list = {h["name"].lower(): h["value"] for h in msg_data.get("payload", {}).get("headers", [])}
                        body = ""
                        payload = msg_data.get("payload", {})
                        if payload.get("body", {}).get("data"):
                            import base64
                            body = base64.urlsafe_b64decode(payload["body"]["data"]).decode("utf-8", errors="replace")[:2000]
                        messages.append({
                            "from": headers_list.get("from", ""),
                            "to": headers_list.get("to", ""),
                            "subject": headers_list.get("subject", ""),
                            "body": body,
                            "date": headers_list.get("date", ""),
                        })
    except Exception as e:
        logger.error(f"Gmail fetch error: {e}")
    return messages


async def start_worker_loop(interval_seconds: int = 300):
    """Main worker loop — runs indefinitely."""
    logger.info(f"Starting worker loop (interval={interval_seconds}s)")
    while True:
        try:
            await poll_all_tenants()
        except Exception as e:
            logger.error(f"Worker loop error: {e}")
        await asyncio.sleep(interval_seconds)
