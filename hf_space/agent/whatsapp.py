import logging
import re
from datetime import datetime

import requests

logger = logging.getLogger("mailpilot.whatsapp")

META_API_VERSION = "21.0"
MAX_BODY_CHARS = 3800


class WhatsAppSendError(RuntimeError):
    pass


def _clean(text):
    return re.sub(r"\s+", " ", (text or "").strip())


def _truncate(text, limit):
    text = (text or "").strip()
    if len(text) <= limit:
        return text
    cut = text[:limit]
    if " " in cut:
        cut = cut.rsplit(" ", 1)[0]
    return cut.rstrip(",.;:") + "..."


def format_email_alert(msg, classification, summary=None):
    when = "unknown time"
    if msg.date is not None:
        when = msg.date.astimezone().strftime("%a %d %b %Y, %H:%M")
    lines = [
        "*IMPORTANT EMAIL*",
        "",
        f"*From:* {_clean(msg.sender_display)}",
        f"*Subject:* {_clean(msg.subject) or '(no subject)'}",
        f"*Received:* {when}",
        f"*Why:* {_clean(classification.summary())}",
        "",
    ]
    if summary:
        lines.append(f"*Gemini summary:* {_clean(summary)}")
        lines.append("")
    excerpt = _truncate(msg.body_text, 700)
    if excerpt:
        lines.append(excerpt)
        lines.append("")
    lines.append(f"_Importance score {classification.score}/100_")
    return "\n".join(lines)


class WhatsAppSender:
    def __init__(self, whatsapp_cfg, token="", twilio_sid="", twilio_auth_token=""):
        self.cfg = whatsapp_cfg
        self.recipients = whatsapp_cfg.recipients()
        self.token = token
        self.twilio_sid = twilio_sid
        self.twilio_auth_token = twilio_auth_token

    def send_email_alert(self, msg, classification, summary=None):
        body = format_email_alert(msg, classification, summary=summary)
        return self.send_text(body)

    def send_text(self, body):
        body = _truncate(body, MAX_BODY_CHARS)
        if not self.recipients:
            raise WhatsAppSendError("no recipient numbers configured")
        failures = []
        for number in self.recipients:
            try:
                if self.cfg.provider == "meta":
                    self._send_meta(body, number)
                elif self.cfg.provider == "twilio":
                    self._send_twilio(body, number)
                else:
                    raise WhatsAppSendError(f"Unknown provider '{self.cfg.provider}'")
            except WhatsAppSendError as exc:
                logger.error("Send to %s failed: %s", number, exc)
                failures.append((number, str(exc)))
        if len(failures) == len(self.recipients):
            raise WhatsAppSendError("; ".join(f"{n}: {e}" for n, e in failures))
        return True

    def _send_meta(self, body, to_number):
        url = f"https://graph.facebook.com/v{META_API_VERSION}/{self.cfg.meta_phone_number_id}/messages"
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to_number,
            "type": "text",
            "text": {"preview_url": True, "body": body},
        }
        try:
            resp = requests.post(
                url,
                headers={
                    "Authorization": f"Bearer {self.token}",
                    "Content-Type": "application/json",
                },
                json=payload,
                timeout=20,
            )
        except requests.RequestException as exc:
            raise WhatsAppSendError(f"Meta API request failed: {exc}") from exc
        if resp.status_code >= 400:
            code = None
            try:
                code = resp.json().get("error", {}).get("code")
            except ValueError:
                pass
            if code == 131047:
                logger.warning("Outside 24h window for %s; falling back to hello_world template", to_number)
                return self._send_meta_template(to_number)
            raise WhatsAppSendError(f"Meta API error {resp.status_code}: {resp.text[:300]}")
        data = resp.json()
        message_id = ""
        try:
            message_id = data["messages"][0]["id"]
        except (KeyError, IndexError, TypeError, ValueError):
            pass
        logger.info("WhatsApp message sent via Meta to %s (id=%s)", to_number, message_id or "?")
        return True

    def _send_meta_template(self, to_number, name="hello_world", language="en_US"):
        url = f"https://graph.facebook.com/v{META_API_VERSION}/{self.cfg.meta_phone_number_id}/messages"
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to_number,
            "type": "template",
            "template": {"name": name, "language": {"code": language}},
        }
        try:
            resp = requests.post(
                url,
                headers={
                    "Authorization": f"Bearer {self.token}",
                    "Content-Type": "application/json",
                },
                json=payload,
                timeout=20,
            )
        except requests.RequestException as exc:
            raise WhatsAppSendError(f"Meta template request failed: {exc}") from exc
        if resp.status_code >= 400:
            raise WhatsAppSendError(f"Meta template error {resp.status_code}: {resp.text[:300]}")
        logger.info("WhatsApp template '%s' sent via Meta to %s", name, to_number)
        return True

    def _send_twilio(self, body, to_number):
        url = f"https://api.twilio.com/2010-04-01/Accounts/{self.twilio_sid}/Messages.json"
        data = {
            "From": f"whatsapp:{self.cfg.twilio_from_number}",
            "To": f"whatsapp:{to_number}",
            "Body": body,
        }
        try:
            resp = requests.post(url, data=data, auth=(self.twilio_sid, self.twilio_auth_token), timeout=20)
        except requests.RequestException as exc:
            raise WhatsAppSendError(f"Twilio request failed: {exc}") from exc
        if resp.status_code >= 400:
            raise WhatsAppSendError(f"Twilio error {resp.status_code}: {resp.text[:300]}")
        logger.info("WhatsApp message sent via Twilio to %s (sid=%s)", to_number, resp.json().get("sid", "?"))
        return True
