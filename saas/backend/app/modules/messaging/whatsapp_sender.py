"""WhatsApp message sender — sends clean alert cards via Meta Cloud API."""
import logging
import aiohttp

logger = logging.getLogger("mailpilot.whatsapp")


async def send_whatsapp_message(
    phone_number: str,
    meta_phone_number_id: str,
    meta_access_token: str,
    subject: str,
    sender: str,
    body: str,
    importance: float = 0.5,
) -> dict:
    """Send a formatted email alert to WhatsApp."""
    emoji = "🟢" if importance > 0.7 else "🟡" if importance > 0.4 else "⚪"
    text = (
        f"{emoji} *New Email Alert*\n\n"
        f"*From:* {sender}\n"
        f"*Subject:* {subject}\n"
        f"*Time:* Check email for full details\n\n"
        f"*Message:*\n{body[:500]}"
    )

    url = f"https://graph.facebook.com/v21.0/{meta_phone_number_id}/messages"
    payload = {
        "messaging_product": "whatsapp",
        "to": phone_number,
        "type": "text",
        "text": {"body": text},
    }
    headers = {
        "Authorization": f"Bearer {meta_access_token}",
        "Content-Type": "application/json",
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, headers=headers, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                data = await resp.json()
                if resp.status == 200 and data.get("messages"):
                    msg_id = data["messages"][0].get("id", "")
                    logger.info(f"WhatsApp sent to {phone_number}: {msg_id}")
                    return {"ok": True, "message_id": msg_id}
                else:
                    error = data.get("error", {}).get("message", str(data))
                    logger.error(f"WhatsApp error: {error}")
                    return {"ok": False, "error": error}
    except Exception as e:
        logger.error(f"WhatsApp send failed: {e}")
        return {"ok": False, "error": str(e)}
