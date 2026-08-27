"""Poll WhatsApp for new messages and respond via AI agent."""
import time
import httpx
import json
import sys

BASE = "http://localhost:8000/api"
PHONE_NUMBER_ID = "1287317304459774"
ACCESS_TOKEN = "EAAO6gp7kDjQBSZAtrKbRNmnJCsnA7GWZBN67Ikvc2KbRJLDSHQGAkQT0hiBfiUahM95XPcy7URAnAWZAZBZBrKri2cMr0PZBhVEKhzYZBA42oPeg7D0xkpMMOtEfm0wXBkXr7fmyBJtTYpc7rWpKwUBPkZCmTlHZAITzL2bf3GMy3nsruR4OOsadoZChqRchvqbdVoDwZDZD"

def get_ai_response(message_text):
    """Get AI response from agent."""
    try:
        resp = httpx.post(f"{BASE}/auth/login", json={"email": "test@test.com", "password": "Test1234!"}, timeout=10)
        token = resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        resp = httpx.get(f"{BASE}/workspaces/", headers=headers)
        ws_id = resp.json()[0]["id"]
        resp = httpx.get(f"{BASE}/agents/workspace/{ws_id}", headers=headers)
        agent_id = resp.json()[0]["id"]
        
        resp = httpx.post(f"{BASE}/agents/{agent_id}/message", headers=headers, json={
            "message": message_text,
            "channel_type": "whatsapp"
        }, timeout=60)
        
        if resp.status_code == 200:
            return resp.json().get("message", "I'm sorry, I couldn't process your message.")
        else:
            return "I'm experiencing technical difficulties. Please try again."
    except Exception as e:
        return "I'm currently unavailable. Please try again later."

def send_whatsapp(to_number, message):
    """Send WhatsApp message via Meta API."""
    resp = httpx.post(
        f"https://graph.facebook.com/v21.0/{PHONE_NUMBER_ID}/messages",
        headers={"Authorization": f"Bearer {ACCESS_TOKEN}", "Content-Type": "application/json"},
        json={"messaging_product": "whatsapp", "to": to_number, "type": "text", "text": {"body": message}},
        timeout=15,
    )
    return resp.status_code == 200

def check_webhook_log():
    """Check recent webhook deliveries from Meta."""
    try:
        resp = httpx.get(
            f"https://graph.facebook.com/v21.0/{PHONE_NUMBER_ID}/messages",
            headers={"Authorization": f"Bearer {ACCESS_TOKEN}"},
            params={"limit": 5},
            timeout=10,
        )
        if resp.status_code == 200:
            return resp.json().get("data", [])
    except:
        pass
    return []

if __name__ == "__main__":
    print("=" * 50)
    print("WhatsApp AI Agent - Polling Mode")
    print("=" * 50)
    print()
    print("Since webhooks can't reach your local server,")
    print("this script processes messages manually.")
    print()
    print("HOW TO USE:")
    print("1. Send a WhatsApp message to +250786508880")
    print("2. Run this script and type the message you sent")
    print("3. The AI will respond on WhatsApp")
    print()
    print("Type 'quit' to exit")
    print("-" * 50)
    
    while True:
        try:
            user_input = input("\nYour message (what you texted): ").strip()
            if user_input.lower() in ["quit", "exit", "q"]:
                break
            if not user_input:
                continue
            
            print(f"\nProcessing: '{user_input}'...")
            response = get_ai_response(user_input)
            print(f"AI Response: {response}")
            
            send = input("Send this response to WhatsApp? (y/n): ").strip().lower()
            if send in ["y", "yes", ""]:
                sent = send_whatsapp("+250786508880", response)
                print(f"WhatsApp sent: {'Yes' if sent else 'Failed'}")
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"Error: {e}")
    
    print("\nGoodbye!")
