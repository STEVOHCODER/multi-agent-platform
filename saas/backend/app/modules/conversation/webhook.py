"""WhatsApp webhook handler — bridges Meta Cloud API to the agent system."""
import logging
import hashlib
import json
from fastapi import APIRouter, Request, HTTPException, Query
from sqlalchemy.orm import Session

from app.modules.core.database import get_db
from app.modules.workspace.models import Workspace
from app.modules.conversation.models import Channel, Contact, Conversation, UniversalMessage
from app.modules.agent.router_engine import route_message

logger = logging.getLogger("mailpilot.whatsapp_webhook")

router = APIRouter(prefix="/api/webhooks", tags=["webhooks"])

# Idempotency: track processed message IDs
_processed_messages: set[str] = set()


@router.post("/whatsapp/{workspace_id}")
async def whatsapp_webhook(workspace_id: str, request: Request):
    """Receive WhatsApp messages from Meta Cloud API webhook."""
    body = await request.json()

    # Handle webhook verification
    if "hub.mode" in body:
        return {"hub.mode": body.get("hub.mode"), "hub.verify_token": body.get("hub.verify_token"), "hub.challenge": body.get("hub.challenge")}

    # Process incoming messages
    entry = body.get("entry", [{}])[0]
    changes = entry.get("changes", [{}])[0]
    value = changes.get("value", {})

    messages = value.get("messages", [])
    contacts = value.get("contacts", [])

    db = next(get_db())
    try:
        # Verify workspace exists
        ws = db.query(Workspace).filter(Workspace.id == workspace_id).first()
        if not ws:
            raise HTTPException(status_code=404, detail="Workspace not found")

        # Get or create channel
        channel = db.query(Channel).filter(
            Channel.workspace_id == workspace_id,
            Channel.channel_type == "whatsapp",
        ).first()

        if not channel:
            channel = Channel(
                workspace_id=workspace_id,
                channel_type="whatsapp",
                name="WhatsApp",
                config={"phone_number_id": entry.get("id", "")},
            )
            db.add(channel)
            db.flush()

        for msg in messages:
            msg_id = msg.get("id", "")

            # Idempotency check
            if msg_id in _processed_messages:
                continue
            _processed_messages.add(msg_id)

            # Prevent duplicate in DB
            existing = db.query(UniversalMessage).filter(
                UniversalMessage.raw_message.contains({"id": msg_id})
            ).first()
            if existing:
                continue

            sender = msg.get("from", "")
            text = ""
            msg_type = msg.get("type", "")

            if msg_type == "text":
                text = msg.get("text", {}).get("body", "")
            elif msg_type == "image":
                text = "[Image received]"
            elif msg_type == "document":
                text = "[Document received]"

            # Get or create contact
            contact_name = ""
            wa_id = ""
            for c in contacts:
                if c.get("wa_id") == sender:
                    contact_name = c.get("profile", {}).get("name", "")
                    wa_id = c.get("wa_id", "")
                    break

            contact = db.query(Contact).filter(
                Contact.workspace_id == workspace_id,
                Contact.external_id == wa_id or Contact.external_id == sender,
            ).first()

            if not contact:
                contact = Contact(
                    workspace_id=workspace_id,
                    external_id=sender,
                    name=contact_name,
                    channel_type="whatsapp",
                )
                db.add(contact)
                db.flush()

            # Get or create conversation
            conversation = db.query(Conversation).filter(
                Conversation.workspace_id == workspace_id,
                Conversation.contact_id == contact.id,
                Conversation.status == "active",
            ).first()

            if not conversation:
                conversation = Conversation(
                    workspace_id=workspace_id,
                    contact_id=contact.id,
                    channel_id=channel.id,
                    channel_type="whatsapp",
                    external_conversation_id=sender,
                )
                db.add(conversation)
                db.flush()

            # Create universal message
            universal_msg = UniversalMessage(
                workspace_id=workspace_id,
                conversation_id=conversation.id,
                channel_id=channel.id,
                channel="whatsapp",
                direction="inbound",
                sender_id=sender,
                sender_name=contact_name,
                text=text,
                raw_message=msg,
            )
            db.add(universal_msg)
            db.commit()
            db.refresh(universal_msg)

            # Route to agent
            try:
                result = await route_message(db, universal_msg)

                # Update message with processing result
                universal_msg.processed = True
                universal_msg.agent_id = result.get("agent_id")
                universal_msg.skill_used = result.get("skill_used")
                universal_msg.confidence = result.get("confidence")

                # Send response if agent produced one
                if result.get("response") and result.get("agent_id"):
                    response_msg = UniversalMessage(
                        workspace_id=workspace_id,
                        conversation_id=conversation.id,
                        channel_id=channel.id,
                        channel="whatsapp",
                        direction="outbound",
                        sender_id="agent",
                        sender_name="AI Agent",
                        text=result["response"],
                    )
                    db.add(response_msg)
                    db.commit()

                    # Send via WhatsApp API
                    try:
                        import httpx
                        from app.modules.core.config import Settings
                        settings = Settings()
                        phone_number_id = settings.whatsapp_phone_number_id
                        token = settings.whatsapp_access_token
                        async with httpx.AsyncClient() as client:
                            await client.post(
                                f"https://graph.facebook.com/v21.0/{phone_number_id}/messages",
                                headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
                                json={"messaging_product": "whatsapp", "to": sender, "type": "text", "text": {"body": result["response"]}},
                                timeout=15,
                            )
                    except Exception as e:
                        logger.error(f"Failed to send WhatsApp response: {e}")

                db.commit()

            except Exception as e:
                logger.error(f"Agent routing error: {e}")
                db.commit()

        return {"ok": True}

    finally:
        db.close()


@router.get("/whatsapp/{workspace_id}")
async def whatsapp_verify(
    workspace_id: str,
    hub_mode: str = Query(None, alias="hub.mode"),
    hub_verify_token: str = Query(None, alias="hub.verify_token"),
    hub_challenge: str = Query(None, alias="hub.challenge"),
):
    """Webhook verification endpoint for Meta."""
    # In production, verify the token against workspace config
    if hub_mode == "subscribe" and hub_challenge:
        return {"hub.challenge": hub_challenge}
    raise HTTPException(status_code=403, detail="Verification failed")
