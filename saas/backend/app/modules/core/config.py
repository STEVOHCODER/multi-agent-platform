import os
from dataclasses import dataclass, field
from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    # Database
    database_url: str = field(default_factory=lambda: os.getenv("DATABASE_URL", "sqlite:///./mailpilot.db"))

    # JWT
    jwt_secret_key: str = field(default_factory=lambda: os.getenv("JWT_SECRET_KEY", "dev-secret-change-in-production"))
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60 * 24

    # Stripe
    stripe_secret_key: str = field(default_factory=lambda: os.getenv("STRIPE_SECRET_KEY", ""))
    stripe_webhook_secret: str = field(default_factory=lambda: os.getenv("STRIPE_WEBHOOK_SECRET", ""))
    stripe_pro_price_id: str = field(default_factory=lambda: os.getenv("STRIPE_PRO_PRICE_ID", ""))
    stripe_enterprise_price_id: str = field(default_factory=lambda: os.getenv("STRIPE_ENTERPRISE_PRICE_ID", ""))

    # Frontend
    frontend_url: str = field(default_factory=lambda: os.getenv("FRONTEND_URL", "http://localhost:5173"))

    # CORS
    cors_origins: list[str] = field(default_factory=lambda: ["http://localhost:5173", "http://localhost:3000"])

    # AI Provider
    ai_provider: str = field(default_factory=lambda: os.getenv("AI_PROVIDER", "openai"))
    openai_api_key: str = field(default_factory=lambda: os.getenv("OPENAI_API_KEY", ""))
    anthropic_api_key: str = field(default_factory=lambda: os.getenv("ANTHROPIC_API_KEY", ""))
    google_api_key: str = field(default_factory=lambda: os.getenv("GOOGLE_API_KEY", ""))
    default_ai_model: str = field(default_factory=lambda: os.getenv("DEFAULT_AI_MODEL", "gpt-4o-mini"))

    # Email
    email_address: str = field(default_factory=lambda: os.getenv("EMAIL_ADDRESS", ""))
    email_password: str = field(default_factory=lambda: os.getenv("EMAIL_PASSWORD", ""))

    # WhatsApp
    whatsapp_access_token: str = field(default_factory=lambda: os.getenv("WHATSAPP_ACCESS_TOKEN", ""))
    whatsapp_phone_number_id: str = field(default_factory=lambda: os.getenv("WHATSAPP_PHONE_NUMBER_ID", ""))
    whatsapp_phone_number: str = field(default_factory=lambda: os.getenv("WHATSAPP_PHONE_NUMBER", ""))
    whatsapp_business_account_id: str = field(default_factory=lambda: os.getenv("WHATSAPP_BUSINESS_ACCOUNT_ID", ""))

    # Meta App (for webhook setup)
    meta_app_id: str = field(default_factory=lambda: os.getenv("META_APP_ID", ""))
    meta_app_secret: str = field(default_factory=lambda: os.getenv("META_APP_SECRET", ""))
    meta_webhook_verify_token: str = field(default_factory=lambda: os.getenv("WHATSAPP_VERIFY_TOKEN", "agent_platform_webhook_verify_2024"))

    # Worker
    poll_interval_seconds: int = 300


settings = Settings()
