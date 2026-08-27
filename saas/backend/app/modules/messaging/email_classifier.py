"""Simple email importance classifier."""
import re


async def classify_email(msg: dict) -> float:
    """Score email importance 0.0-1.0."""
    subject = (msg.get("subject") or "").lower()
    body = (msg.get("body") or "").lower()
    text = subject + " " + body

    score = 0.5

    urgent = ["urgent", "asap", "immediately", "deadline", "overdue", "critical", "emergency"]
    if any(w in text for w in urgent):
        score += 0.3

    action = ["action required", "please respond", "reply", "confirm", "decision needed"]
    if any(w in text for w in action):
        score += 0.2

    spam = ["unsubscribe", "newsletter", "promotion", "sale", "offer", "winner", "congratulations"]
    if any(w in text for w in spam):
        score -= 0.3

    attachments = ["attachment", "attached", "file attached"]
    if any(w in text for w in attachments):
        score += 0.1

    return max(0.0, min(1.0, score))
