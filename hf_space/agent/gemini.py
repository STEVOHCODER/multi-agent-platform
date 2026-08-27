import json
import logging
import re
import time

import requests

logger = logging.getLogger("mailpilot.gemini")

API_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
MODEL = "gemini-2.5-flash"


class GeminiClient:
    def __init__(self, api_key, model=MODEL):
        self.api_key = api_key
        self.model = model

    def _generate(self, prompt, temperature=0.2, max_tokens=512):
        payload = {
            "contents": [{"role": "user", "parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_tokens,
            },
        }
        url = API_URL.format(model=self.model)
        last_error = None
        for attempt in range(3):
            try:
                resp = requests.post(url, params={"key": self.api_key}, json=payload, timeout=25)
                if resp.status_code < 400:
                    parts = (
                        resp.json()
                        .get("candidates", [{}])[0]
                        .get("content", {})
                        .get("parts", [])
                    )
                    text = "".join(p.get("text", "") for p in parts).strip()
                    return text or None
                last_error = f"{resp.status_code}: {resp.text[:150]}"
                if resp.status_code in (429, 500, 503):
                    time.sleep(2 * (attempt + 1))
                    continue
                break
            except Exception as exc:
                last_error = str(exc)
                time.sleep(2 * (attempt + 1))
        logger.warning("Gemini failed after retries (%s); continuing without AI", last_error)
        return None

    def summarize(self, msg, max_words=55):
        excerpt = (msg.body_text or "").strip().replace("\r", "")[:4000]
        prompt = (
            "Summarize this email for a WhatsApp alert. Plain text only, no markdown. "
            f"Maximum {max_words} words. Capture: what it is about, any action required, "
            "any deadline, any amounts or codes mentioned.\n\n"
            f"From: {msg.sender_display}\n"
            f"Subject: {msg.subject}\n\n{excerpt}"
        )
        summary = self._generate(prompt)
        if not summary:
            return None
        summary = re.sub(r"\s+", " ", summary).strip()
        words = summary.split(" ")
        if len(words) > max_words:
            summary = " ".join(words[:max_words]) + "..."
        return summary

    def rate_importance(self, msg):
        excerpt = (msg.body_text or "").strip().replace("\r", "")[:1500]
        prompt = (
            "You rate how important an inbound email is to its recipient on a 0-10 scale. "
            "10 = must act now (security alerts, legal, money, meetings, personal requests from real people). "
            "0 = spam, marketing, automated notifications with no action needed. "
            'Reply with JSON only: {"rating": <0-10>, "reason": "<max 8 words>"}. \n\n'
            f"From: {msg.sender_display}\n"
            f"Subject: {msg.subject}\n\n{excerpt}"
        )
        raw = self._generate(prompt, temperature=0)
        if not raw:
            return None
        try:
            match = re.search(r"\{.*\}", raw, re.DOTALL)
            data = json.loads(match.group(0))
            rating = max(0, min(10, int(data.get("rating", 0))))
            reason = str(data.get("reason", ""))[:60]
            return rating, reason
        except (ValueError, AttributeError, TypeError) as exc:
            logger.warning("Gemini rating parse failed: %s (%r)", exc, raw[:120])
            return None
