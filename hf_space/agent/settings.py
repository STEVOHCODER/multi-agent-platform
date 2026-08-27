import os
from dataclasses import dataclass, field
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent

ENV_KEYS = {
    "EMAIL_ADDRESS": "email_address",
    "EMAIL_PASSWORD": "email_password",
    "GMAIL_CLIENT_ID": "gmail_client_id",
    "GMAIL_CLIENT_SECRET": "gmail_client_secret",
    "WHATSAPP_TOKEN": "whatsapp_token",
    "TWILIO_ACCOUNT_SID": "twilio_sid",
    "TWILIO_AUTH_TOKEN": "twilio_auth_token",
    "GEMINI_API_KEY": "gemini_api_key",
    "OPENAI_API_KEY": "openai_api_key",
}


def load_dotenv(path):
    path = Path(path)
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


@dataclass
class EmailConfig:
    host: str = "imap.gmail.com"
    port: int = 993
    mailbox: str = "INBOX"
    backend: str = "auto"
    lookback_hours: int = 24
    batch_size: int = 25


@dataclass
class WhatsAppConfig:
    provider: str = "meta"
    to_number: str = ""
    to_numbers: list = field(default_factory=list)
    meta_phone_number_id: str = ""
    twilio_from_number: str = ""

    def recipients(self):
        numbers = []
        for n in [self.to_number] + list(self.to_numbers):
            n = (n or "").strip()
            if n and n not in numbers:
                numbers.append(n)
        return numbers


@dataclass
class ClassifierConfig:
    min_score: int = 40
    use_llm: bool = True
    summarize: bool = True
    vip_senders: list = field(default_factory=list)
    blocked_senders: list = field(default_factory=list)
    urgent_keywords: list = field(default_factory=list)
    security_keywords: list = field(default_factory=list)
    finance_keywords: list = field(default_factory=list)
    meeting_keywords: list = field(default_factory=list)
    personal_keywords: list = field(default_factory=list)
    noise_keywords: list = field(default_factory=list)


@dataclass
class AgentConfig:
    interval_seconds: int = 300
    idle_timeout_seconds: int = 1500
    max_per_cycle: int = 5
    state_file: str = "state.json"
    log_file: str = "logs/agent.log"
    log_level: str = "INFO"


@dataclass
class Settings:
    email: EmailConfig
    whatsapp: WhatsAppConfig
    classifier: ClassifierConfig
    agent: AgentConfig
    email_address: str = ""
    email_password: str = ""
    gmail_client_id: str = ""
    gmail_client_secret: str = ""
    gemini_api_key: str = ""
    whatsapp_token: str = ""
    twilio_sid: str = ""
    twilio_auth_token: str = ""
    openai_api_key: str = ""

    def missing_requirements(self):
        problems = []
        if not self.email_address:
            problems.append("EMAIL_ADDRESS is not set (.env)")
        if not self.email_password:
            problems.append("EMAIL_PASSWORD is not set (.env)")
        if not self.whatsapp.to_number and not self.whatsapp.to_numbers:
            problems.append("whatsapp.to_number (or to_numbers) is not set (config.yaml)")
        if self.whatsapp.provider == "meta":
            if not self.whatsapp_token:
                problems.append("WHATSAPP_TOKEN is not set (.env)")
            if not self.whatsapp.meta_phone_number_id:
                problems.append("whatsapp.meta_phone_number_id is not set (config.yaml)")
        elif self.whatsapp.provider == "twilio":
            if not self.twilio_sid or not self.twilio_auth_token:
                problems.append("TWILIO_ACCOUNT_SID / TWILIO_AUTH_TOKEN are not set (.env)")
            if not self.whatsapp.twilio_from_number:
                problems.append("whatsapp.twilio_from_number is not set (config.yaml)")
        else:
            problems.append(f"unknown whatsapp provider '{self.whatsapp.provider}' (use 'meta' or 'twilio')")
        return problems


def _section(raw, key):
    value = raw.get(key)
    return value if isinstance(value, dict) else {}


def _list(section, key, fallback):
    value = section.get(key)
    if isinstance(value, list):
        return [str(v).lower() for v in value]
    return fallback


def load_settings(config_path=None):
    load_dotenv(Path(ROOT) / ".env")
    path = Path(config_path) if config_path else Path(ROOT) / "config.yaml"
    raw = {}
    if path.exists():
        raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}

    e = _section(raw, "email")
    w = _section(raw, "whatsapp")
    c = _section(raw, "classifier")
    a = _section(raw, "agent")

    email_cfg = EmailConfig(
        host=e.get("host", "imap.gmail.com"),
        port=int(e.get("port", 993)),
        mailbox=e.get("mailbox", "INBOX"),
        backend=e.get("backend", "auto"),
        lookback_hours=int(e.get("lookback_hours", 24)),
        batch_size=int(e.get("batch_size", 25)),
    )
    whatsapp_cfg = WhatsAppConfig(
        provider=w.get("provider", "meta"),
        to_number=str(w.get("to_number", "")),
        to_numbers=[str(n) for n in w.get("to_numbers", [])] if isinstance(w.get("to_numbers"), list) else [],
        meta_phone_number_id=str(w.get("meta_phone_number_id", "")),
        twilio_from_number=str(w.get("twilio_from_number", "")),
    )

    default_urgent = ["urgent", "asap", "action required", "immediately", "deadline",
                      "overdue", "time sensitive", "expires today", "last reminder", "final notice"]
    default_security = ["security alert", "verify your account", "password reset",
                        "unusual sign-in", "login attempt", "verification code", "one-time code"]
    default_finance = ["invoice", "payment received", "payment failed", "receipt",
                       "transaction", "refund", "billing", "wire transfer", "salary", "invoice overdue"]
    default_meeting = ["meeting invitation", "calendar invite", "interview", "appointment",
                       "call scheduled", "rescheduled", "rsvp", "zoom invite", "meeting request"]
    default_personal = ["are you available", "can you call", "please review", "for you",
                        "following up with you", "checking in"]
    default_noise = ["unsubscribe", "newsletter", "digest", "% off", "discount", "promo",
                     "limited time offer", "webinar", "deal of the day", "flash sale",
                     "you are receiving this email"]

    classifier_cfg = ClassifierConfig(
        min_score=int(c.get("min_score", 40)),
        use_llm=bool(c.get("use_llm", True)),
        summarize=bool(c.get("summarize", True)),
        vip_senders=_list(c, "vip_senders", []),
        blocked_senders=_list(c, "blocked_senders", []),
        urgent_keywords=_list(c, "urgent_keywords", default_urgent),
        security_keywords=_list(c, "security_keywords", default_security),
        finance_keywords=_list(c, "finance_keywords", default_finance),
        meeting_keywords=_list(c, "meeting_keywords", default_meeting),
        personal_keywords=_list(c, "personal_keywords", default_personal),
        noise_keywords=_list(c, "noise_keywords", default_noise),
    )

    agent_cfg = AgentConfig(
        interval_seconds=int(a.get("interval_seconds", 300)),
        idle_timeout_seconds=int(a.get("idle_timeout_seconds", 1500)),
        max_per_cycle=int(a.get("max_per_cycle", 5)),
        state_file=a.get("state_file", "state.json"),
        log_file=a.get("log_file", "logs/agent.log"),
        log_level=a.get("log_level", "INFO").upper(),
    )

    secrets = {env_key: os.environ.get(env_key, "") for env_key in ENV_KEYS}
    return Settings(
        email=email_cfg,
        whatsapp=whatsapp_cfg,
        classifier=classifier_cfg,
        agent=agent_cfg,
        **{ENV_KEYS[k]: v for k, v in secrets.items()},
    )
