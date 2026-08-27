"""Simulate WhatsApp incoming message -> AI agent -> WhatsApp response."""
import asyncio
import httpx
import json

BASE = "http://localhost:8000/api"

async def simulate_whatsapp_message(sender_phone: str, message_text: str):
    """Simulate receiving a WhatsApp message and responding."""
    print(f"\n{'='*60}")
    print(f"INCOMING WhatsApp from {sender_phone}")
    print(f"Message: {message_text}")
    print(f"{'='*60}")

    # 1. Login
    async with httpx.AsyncClient() as client:
        resp = await client.post(f"{BASE}/auth/login", json={
            "email": "test@test.com",
            "password": "Test1234!"
        })
        token = resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # 2. Get workspace and agent
        resp = await client.get(f"{BASE}/workspaces/", headers=headers)
        ws_id = resp.json()[0]["id"]

        resp = await client.get(f"{BASE}/agents/workspace/{ws_id}", headers=headers)
        agents = resp.json()
        if not agents:
            print("No agent found!")
            return

        agent = agents[0]
        agent_id = agent["id"]
        print(f"\nAgent: {agent['name']} (model: {agent['model']})")

        # 3. Send message to agent
        print(f"\nProcessing through AI agent...")
        resp = await client.post(f"{BASE}/agents/{agent_id}/message", headers=headers, json={
            "message": message_text,
            "channel_type": "whatsapp",
            "sender_phone": sender_phone,
        }, timeout=60)

        if resp.status_code == 200:
            result = resp.json()
            ai_response = result.get("message", "")
            print(f"\nAI Response: {ai_response}")

            # 4. Send response back via WhatsApp
            print(f"\nSending response via WhatsApp to {sender_phone}...")
            from agent.whatsapp import WhatsAppSender
            from agent.settings import load_settings

            settings = load_settings()
            sender = WhatsAppSender(
                settings.whatsapp,
                token=settings.whatsapp_token,
            )

            # Override recipients to send to the sender's number
            sender.recipients = [sender_phone]
            sent = sender.send_text(ai_response)
            print(f"WhatsApp sent: {sent}")
        else:
            print(f"Error: {resp.status_code} - {resp.text[:200]}")


async def main():
    # Simulate different client messages
    test_messages = [
        ("+250786508880", "Hello, I need help with my order"),
        ("+250786508880", "I want a refund for order #12345"),
        ("+250786508880", "What is your return policy?"),
    ]

    for phone, msg in test_messages:
        await simulate_whatsapp_message(phone, msg)
        await asyncio.sleep(2)  # Rate limit


if __name__ == "__main__":
    asyncio.run(main())
