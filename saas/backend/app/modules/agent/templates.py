"""Built-in agent templates — one-click agent creation."""
from dataclasses import dataclass, field


@dataclass(frozen=True)
class AgentTemplate:
    id: str
    name: str
    description: str
    model: str
    system_instructions: str
    skills: list[str]
    channels: list[str]
    response_mode: str
    auto_reply: bool
    memory_enabled: bool


AGENT_TEMPLATES: dict[str, AgentTemplate] = {
    "customer_support": AgentTemplate(
        id="customer_support",
        name="Customer Support Agent",
        description="Answers customer questions, handles FAQs, and escalates complex issues to humans.",
        model="gpt-4o-mini",
        system_instructions=(
            "You are a helpful customer support agent. "
            "Answer questions using the provided knowledge base. "
            "If you are unsure or the question is complex, escalate to a human agent. "
            "Always be polite and professional."
        ),
        skills=["customer_reply", "detect_intent", "search_knowledge", "search_memory", "save_memory", "escalate_to_human"],
        channels=["whatsapp", "email"],
        response_mode="auto_escalation",
        auto_reply=True,
        memory_enabled=True,
    ),
    "email_monitor": AgentTemplate(
        id="email_monitor",
        name="Email Monitor Agent",
        description="Monitors email, classifies importance, and sends WhatsApp alerts for important messages.",
        model="gpt-4o-mini",
        system_instructions=(
            "You are an email monitoring agent. "
            "Classify incoming emails by importance and urgency. "
            "Forward important emails as WhatsApp notifications with clear summaries."
        ),
        skills=["email_classification", "email_summary", "email_to_whatsapp"],
        channels=["email"],
        response_mode="auto",
        auto_reply=False,
        memory_enabled=False,
    ),
    "settlement": AgentTemplate(
        id="settlement",
        name="Settlement Agent",
        description="Tracks payment requests, matches settlements, and generates reconciliation reports.",
        model="gpt-4o-mini",
        system_instructions=(
            "You are a financial settlement agent. "
            "Extract payment details from messages. "
            "Match confirmations against unsettled transactions. "
            "Never guess — if uncertain, mark for review. "
            "Generate daily settlement reports."
        ),
        skills=["extract_payment", "match_settlement", "create_transaction", "find_unsettled", "reconcile_transactions", "generate_report", "search_memory", "save_memory"],
        channels=["whatsapp"],
        response_mode="auto_escalation",
        auto_reply=True,
        memory_enabled=True,
    ),
    "notification": AgentTemplate(
        id="notification",
        name="Notification Agent",
        description="Sends alerts, reminders, and scheduled reports to configured channels.",
        model="gpt-4o-mini",
        system_instructions=(
            "You are a notification agent. "
            "Send timely alerts and reminders. "
            "Keep messages concise and actionable."
        ),
        skills=["send_whatsapp", "send_email", "detect_reminder"],
        channels=["whatsapp", "email"],
        response_mode="auto",
        auto_reply=False,
        memory_enabled=False,
    ),
    "general_assistant": AgentTemplate(
        id="general_assistant",
        name="General AI Assistant",
        description="A versatile assistant for conversation, knowledge search, and basic tasks.",
        model="gpt-4o",
        system_instructions=(
            "You are a general-purpose AI assistant. "
            "Help with questions, look up knowledge, and assist with tasks. "
            "If something is outside your scope, escalate to a human."
        ),
        skills=["customer_reply", "detect_intent", "search_knowledge", "search_memory", "save_memory", "summarize_message", "escalate_to_human"],
        channels=["whatsapp", "email"],
        response_mode="auto_escalation",
        auto_reply=True,
        memory_enabled=True,
    ),
}
