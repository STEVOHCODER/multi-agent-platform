from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import httpx

from app.modules.core.database import get_db
from app.modules.core.config import settings
from app.modules.auth.models import User
from app.modules.auth.service import get_current_user
from app.modules.workspace.models import WorkspaceMember
from app.modules.conversation.models import Channel, Contact, Conversation, UniversalMessage, ConversationMemory
from app.modules.conversation.schemas import (
    ChannelCreate, ChannelResponse,
    ContactCreate, ContactResponse,
    UniversalMessageCreate, UniversalMessageResponse,
    ConversationResponse, MemoryCreate, MemoryResponse,
)

router = APIRouter(prefix="/api/conversations", tags=["conversations"])


def _check_workspace(workspace_id: str, user: User, db: Session):
    member = db.query(WorkspaceMember).filter(
        WorkspaceMember.workspace_id == workspace_id,
        WorkspaceMember.user_id == user.id,
        WorkspaceMember.is_active == True,
    ).first()
    if not member:
        raise HTTPException(status_code=403, detail="Not a member of this workspace")
    return member


# ── Channels ───────────────────────────────────────────────────────
@router.post("/workspace/{workspace_id}/channels", response_model=ChannelResponse)
def create_channel(
    workspace_id: str,
    data: ChannelCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _check_workspace(workspace_id, user, db)
    ch = Channel(workspace_id=workspace_id, channel_type=data.channel_type, name=data.name, config=data.config)
    db.add(ch)
    db.commit()
    db.refresh(ch)
    return ChannelResponse.model_validate(ch)


@router.get("/workspace/{workspace_id}/channels", response_model=list[ChannelResponse])
def list_channels(
    workspace_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _check_workspace(workspace_id, user, db)
    channels = db.query(Channel).filter(Channel.workspace_id == workspace_id).all()
    return [ChannelResponse.model_validate(c) for c in channels]


# ── Contacts ───────────────────────────────────────────────────────
@router.post("/workspace/{workspace_id}/contacts", response_model=ContactResponse)
def create_contact(
    workspace_id: str,
    data: ContactCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _check_workspace(workspace_id, user, db)
    contact = Contact(workspace_id=workspace_id, **data.model_dump())
    db.add(contact)
    db.commit()
    db.refresh(contact)
    return ContactResponse.model_validate(contact)


@router.get("/workspace/{workspace_id}/contacts", response_model=list[ContactResponse])
def list_contacts(
    workspace_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _check_workspace(workspace_id, user, db)
    contacts = db.query(Contact).filter(Contact.workspace_id == workspace_id).all()
    return [ContactResponse.model_validate(c) for c in contacts]


# ── Messages ───────────────────────────────────────────────────────
@router.post("/workspace/{workspace_id}/messages", response_model=UniversalMessageResponse)
def create_message(
    workspace_id: str,
    data: UniversalMessageCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _check_workspace(workspace_id, user, db)
    msg = UniversalMessage(workspace_id=workspace_id, **data.model_dump())
    db.add(msg)
    db.commit()
    db.refresh(msg)
    return UniversalMessageResponse.model_validate(msg)


@router.get("/workspace/{workspace_id}/messages", response_model=list[UniversalMessageResponse])
def list_messages(
    workspace_id: str,
    conversation_id: str = None,
    limit: int = 50,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _check_workspace(workspace_id, user, db)
    q = db.query(UniversalMessage).filter(UniversalMessage.workspace_id == workspace_id)
    if conversation_id:
        q = q.filter(UniversalMessage.conversation_id == conversation_id)
    msgs = q.order_by(UniversalMessage.created_at.desc()).limit(limit).all()
    return [UniversalMessageResponse.model_validate(m) for m in msgs]


# ── Memory ─────────────────────────────────────────────────────────
@router.post("/workspace/{workspace_id}/memory", response_model=MemoryResponse)
def save_memory(
    workspace_id: str,
    data: MemoryCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _check_workspace(workspace_id, user, db)
    mem = ConversationMemory(workspace_id=workspace_id, **data.model_dump())
    db.add(mem)
    db.commit()
    db.refresh(mem)
    return MemoryResponse.model_validate(mem)


@router.get("/workspace/{workspace_id}/memory", response_model=list[MemoryResponse])
def search_memory(
    workspace_id: str,
    query: str = "",
    memory_type: str = None,
    category: str = None,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _check_workspace(workspace_id, user, db)
    q = db.query(ConversationMemory).filter(ConversationMemory.workspace_id == workspace_id)
    if memory_type:
        q = q.filter(ConversationMemory.memory_type == memory_type)
    if category:
        q = q.filter(ConversationMemory.category == category)
    if query:
        q = q.filter(ConversationMemory.content.contains(query))
    memories = q.order_by(ConversationMemory.created_at.desc()).limit(100).all()
    return [MemoryResponse.model_validate(m) for m in memories]


# ── Quick Connect (using .env credentials) ───────────────────────
@router.post("/workspace/{workspace_id}/quick-connect/whatsapp", response_model=ChannelResponse)
def quick_connect_whatsapp(
    workspace_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Auto-connect WhatsApp using credentials from .env file."""
    _check_workspace(workspace_id, user, db)

    access_token = settings.whatsapp_access_token
    phone_number_id = settings.whatsapp_phone_number_id

    if not access_token or not phone_number_id:
        raise HTTPException(status_code=400, detail="WhatsApp credentials not configured in .env")

    # Check if already connected
    existing = db.query(Channel).filter(
        Channel.workspace_id == workspace_id,
        Channel.channel_type == "whatsapp",
    ).first()
    if existing:
        existing.config = {
            "access_token": access_token,
            "phone_number_id": phone_number_id,
            "business_account_id": settings.whatsapp_business_account_id,
            "phone_number": settings.whatsapp_phone_number,
        }
        db.commit()
        db.refresh(existing)
        return ChannelResponse.model_validate(existing)

    ch = Channel(
        workspace_id=workspace_id,
        channel_type="whatsapp",
        name="WhatsApp",
        config={
            "access_token": access_token,
            "phone_number_id": phone_number_id,
            "business_account_id": settings.whatsapp_business_account_id,
            "phone_number": settings.whatsapp_phone_number,
        },
    )
    db.add(ch)
    db.commit()
    db.refresh(ch)
    return ChannelResponse.model_validate(ch)


@router.post("/workspace/{workspace_id}/quick-connect/email", response_model=ChannelResponse)
def quick_connect_email(
    workspace_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Auto-connect Email using credentials from .env file."""
    _check_workspace(workspace_id, user, db)

    email_address = settings.email_address
    if not email_address:
        raise HTTPException(status_code=400, detail="Email credentials not configured in .env")

    existing = db.query(Channel).filter(
        Channel.workspace_id == workspace_id,
        Channel.channel_type == "email",
    ).first()
    if existing:
        existing.config = {"address": email_address}
        db.commit()
        db.refresh(existing)
        return ChannelResponse.model_validate(existing)

    ch = Channel(
        workspace_id=workspace_id,
        channel_type="email",
        name="Email",
        config={"address": email_address},
    )
    db.add(ch)
    db.commit()
    db.refresh(ch)
    return ChannelResponse.model_validate(ch)


# ── Auto Webhook Setup via Meta API ─────────────────────────────
@router.post("/workspace/{workspace_id}/setup-webhook")
async def setup_webhook(
    workspace_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Automatically configure the WhatsApp webhook using Meta Graph API."""
    _check_workspace(workspace_id, user, db)

    app_id = settings.meta_app_id
    app_secret = settings.meta_app_secret
    verify_token = settings.meta_webhook_verify_token
    callback_url = f"{settings.api_url}/api/webhooks/whatsapp/{workspace_id}"

    if not app_id or not app_secret:
        raise HTTPException(
            status_code=400,
            detail="META_APP_ID and META_APP_SECRET must be set in .env. "
                   "Get these from Meta Developer Console → Your App → Settings → Basic."
        )

    # Meta requires HTTPS for webhook URLs
    if not callback_url.startswith("https://"):
        raise HTTPException(
            status_code=400,
            detail=f"Meta requires HTTPS for webhook URLs. Your current URL: {callback_url}\n\n"
                   "To fix this, run ngrok to get a public HTTPS URL:\n"
                   "1. Download ngrok: https://ngrok.com/download\n"
                   "2. Run: ngrok http 8000\n"
                   "3. Copy the https://xxx.ngrok.io URL\n"
                   "4. Set API_URL=https://xxx.ngrok.io in your .env file\n"
                   "5. Restart the backend\n"
                   "6. Try again"
        )

    async with httpx.AsyncClient() as client:
        # Step 1: Get app access token
        token_url = "https://graph.facebook.com/v21.0/oauth/access_token"
        resp = await client.get(token_url, params={
            "client_id": app_id,
            "client_secret": app_secret,
            "grant_type": "client_credentials",
        })
        if resp.status_code != 200:
            raise HTTPException(status_code=400, detail=f"Failed to get app token: {resp.text}")
        app_access_token = resp.json()["access_token"]

        # Step 2: Subscribe to webhook
        subscribe_url = f"https://graph.facebook.com/v21.0/{app_id}/subscriptions"
        resp = await client.post(subscribe_url, data={
            "callback_url": callback_url,
            "verify_token": verify_token,
            "fields": "messages,messaging_postbacks",
            "object": "whatsapp",
            "access_token": app_access_token,
        })
        result = resp.json()
        if resp.status_code != 200 or result.get("error"):
            error_msg = result.get("error", {}).get("message", str(result))
            raise HTTPException(status_code=400, detail=f"Webhook setup failed: {error_msg}")

    return {
        "success": True,
        "message": "Webhook configured successfully!",
        "callback_url": callback_url,
        "verify_token": verify_token,
    }


@router.get("/workspace/{workspace_id}/webhook-status")
async def webhook_status(
    workspace_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Check webhook subscription status."""
    _check_workspace(workspace_id, user, db)

    app_id = settings.meta_app_id
    app_secret = settings.meta_app_secret

    if not app_id or not app_secret:
        return {"configured": False, "message": "META_APP_ID and META_APP_SECRET not set"}

    try:
        async with httpx.AsyncClient() as client:
            # Get app access token
            token_url = "https://graph.facebook.com/v21.0/oauth/access_token"
            resp = await client.get(token_url, params={
                "client_id": app_id,
                "client_secret": app_secret,
                "grant_type": "client_credentials",
            })
            if resp.status_code != 200:
                return {"configured": False, "message": "Could not authenticate with Meta"}
            app_access_token = resp.json()["access_token"]

            # Check subscriptions
            sub_url = f"https://graph.facebook.com/v21.0/{app_id}/subscriptions"
            resp = await client.get(sub_url, params={"access_token": app_access_token})
            result = resp.json()
            subscriptions = result.get("data", [])
    except Exception as e:
        return {"configured": False, "message": f"Connection error: {str(e)}"}

    return {
        "configured": True,
        "app_id": app_id,
        "subscriptions": subscriptions,
        "callback_url": f"{settings.api_url}/api/webhooks/whatsapp/{workspace_id}",
    }
