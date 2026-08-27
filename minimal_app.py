import os
from fastapi import FastAPI, Request, Query
import httpx

app = FastAPI()

WHATSAPP_TOKEN = os.getenv("WHATSAPP_ACCESS_TOKEN", "")
PHONE_NUMBER_ID = os.getenv("WHATSAPP_PHONE_NUMBER_ID", "1287317304459774")
VERIFY_TOKEN = os.getenv("META_WEBHOOK_VERIFY_TOKEN", "agent_platform_webhook_verify_2024")
OPENROUTER_KEY = os.getenv("OPENROUTER_API_KEY", "")

@app.get("/api/health")
def health():
    return {"status": "ok"}

@app.get("/api/webhooks/whatsapp/test")
async def verify(hub_mode: str = Query(None, alias="hub.mode"), hub_verify_token: str = Query(None, alias="hub.verify_token"), hub_challenge: str = Query(None, alias="hub.challenge")):
    if hub_mode == "subscribe" and hub_verify_token == VERIFY_TOKEN:
        return {"hub.challenge": hub_challenge}
    return {"error": "verification failed"}

async def get_ai_response(message: str) -> str:
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post("https://openrouter.ai/api/v1/chat/completions",
                headers={"Authorization": f"Bearer {OPENROUTER_KEY}", "Content-Type": "application/json"},
                json={"model": "nvidia/nemotron-3.5-lightning:free", "messages": [
                    {"role": "system", "content": "You are a helpful customer support agent. Be concise and professional."},
                    {"role": "user", "content": message}
                ], "max_tokens": 300},
                timeout=30)
            return resp.json()["choices"][0]["message"]["content"]
    except Exception as e:
        return "Thank you for your message. A support agent will assist you shortly."

async def send_whatsapp(to: str, text: str):
    async with httpx.AsyncClient() as client:
        await client.post(f"https://graph.facebook.com/v21.0/{PHONE_NUMBER_ID}/messages",
            headers={"Authorization": f"Bearer {WHATSAPP_TOKEN}", "Content-Type": "application/json"},
            json={"messaging_product": "whatsapp", "to": to, "type": "text", "text": {"body": text}},
            timeout=15)

@app.post("/api/webhooks/whatsapp/test")
async def webhook(request: Request):
    body = await request.json()
    entry = body.get("entry", [{}])[0]
    changes = entry.get("changes", [{}])[0]
    value = changes.get("value", {})
    messages = value.get("messages", [])

    for msg in messages:
        sender = msg.get("from", "")
        text = msg.get("text", {}).get("body", "") if msg.get("type") == "text" else ""
        if text and sender:
            response = await get_ai_response(text)
            await send_whatsapp(sender, response)

    return {"ok": True}
