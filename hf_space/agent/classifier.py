import json
import logging
import re
from dataclasses import dataclass, field

logger = logging.getLogger("mailpilot.classifier")

CATEGORY_WEIGHTS = {
    "urgent": 28,
    "security": 32,
    "finance": 22,
    "meetings": 20,
    "personal": 16,
}
NOISE_PENALTY = -45
AUTOMATED_PENALTY = -18
DIRECT_BONUS = 12
VIP_BONUS = 60
ATTACHMENT_BONUS = 5


@dataclass
class Classification:
    score: int = 0
    important: bool = False
    reasons: list = field(default_factory=list)

    def summary(self):
        return ", ".join(self.reasons[:3]) if self.reasons else "no strong signals"


class ImportanceClassifier:
    def __init__(self, cfg, owner_email="", openai_api_key="", gemini_client=None):
        self.cfg = cfg
        self.owner_email = (owner_email or "").lower()
        self.openai_api_key = openai_api_key or ""
        self.gemini = gemini_client
        self.vip = {v.strip().lower() for v in cfg.vip_senders if v.strip()}
        self.blocked = {b.strip().lower() for b in cfg.blocked_senders if b.strip()}
        self.categories = {
            "urgent": cfg.urgent_keywords,
            "security": cfg.security_keywords,
            "finance": cfg.finance_keywords,
            "meetings": cfg.meeting_keywords,
            "personal": cfg.personal_keywords,
        }
        self.noise_keywords = list(cfg.noise_keywords)
        self.automated_re = re.compile(
            r"^(no-?reply|donotreply|notifications?|newsletter|mailer-daemon|updates?|alerts?|marketing)@"
        )

    def classify(self, msg):
        if not msg.sender_email:
            return Classification(score=0, important=False, reasons=["missing sender"])
        if msg.sender_email in self.blocked:
            return Classification(score=-1000, important=False, reasons=["blocked sender"])

        score = 0
        reasons = []
        haystack = f"{msg.subject}\n{msg.body_text[:2500]}".lower()

        if msg.sender_email in self.vip:
            score += VIP_BONUS
            reasons.append("VIP sender")

        for category, keywords in self.categories.items():
            hits = [k for k in keywords if k and k in haystack]
            if hits:
                weight = CATEGORY_WEIGHTS[category]
                bonus = min(weight * len(hits), weight * 2)
                score += bonus
                shown = ", ".join(hits[:3])
                reasons.append(f"{category}: {shown}")

        noise_hits = [k for k in self.noise_keywords if k and k in haystack]
        if noise_hits or msg.has_list_unsubscribe:
            score += NOISE_PENALTY
            label = ", ".join(noise_hits[:3]) if noise_hits else "list-unsubscribe header"
            reasons.append(f"bulk/promotional ({label})")

        if self.automated_re.match(msg.sender_email) and msg.sender_email not in self.vip:
            score += AUTOMATED_PENALTY
            reasons.append("automated sender")

        if self.owner_email and self.owner_email in msg.to_addresses:
            score += DIRECT_BONUS
            reasons.append("sent directly to you")

        if msg.has_attachments:
            score += ATTACHMENT_BONUS

        llm_rating = None
        if self.cfg.use_llm:
            if self.gemini is not None:
                llm_rating = self._gemini_rating(msg)
            elif self.openai_api_key:
                llm_rating = self._llm_rating(msg)
        if llm_rating is not None:
            rating, note = llm_rating
            score = max(score, rating * 10)
            reasons.append(f"AI review: {note}")

        score = max(0, min(100, score))
        important = score >= self.cfg.min_score
        return Classification(score=score, important=important, reasons=reasons)

    def _gemini_rating(self, msg):
        try:
            return self.gemini.rate_importance(msg)
        except Exception as exc:
            logger.warning("Gemini rating error, falling back to rules: %s", exc)
            return None

    def _llm_rating(self, msg):
        try:
            import requests
        except ImportError:
            return None
        excerpt = (msg.body_text or "").strip().replace("\r", "")[:1200]
        user_prompt = (
            f"From: {msg.sender_display}\n"
            f"Subject: {msg.subject}\n"
            f"Body excerpt:\n{excerpt}"
        )
        system_prompt = (
            "You rate how important an inbound email is to its recipient on a 0-10 scale. "
            "10 = must act now (security alerts, legal, money, meetings, personal requests from real people). "
            "0 = spam, marketing, automated notifications with no action needed. "
            'Reply with JSON only: {"rating": <0-10>, "reason": "<max 8 words>"}'
        )
        try:
            resp = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.openai_api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "gpt-4o-mini",
                    "temperature": 0,
                    "response_format": {"type": "json_object"},
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                },
                timeout=15,
            )
            resp.raise_for_status()
            content = resp.json()["choices"][0]["message"]["content"]
            data = json.loads(content)
            rating = max(0, min(10, int(data.get("rating", 0))))
            reason = str(data.get("reason", ""))[:60]
            return rating, reason
        except Exception as exc:
            logger.warning("LLM classification failed, falling back to rules: %s", exc)
            return None
