"""Global skill registry — defines all available skills and their metadata."""
from typing import Any


class SkillDef:
    """Definition of a skill (not a DB record — this is the runtime spec)."""
    def __init__(
        self,
        name: str,
        display_name: str,
        description: str,
        category: str,
        input_schema: dict | None = None,
        output_schema: dict | None = None,
        config_schema: dict | None = None,
        required_permissions: list[str] | None = None,
        confidence_threshold: int = 70,
    ):
        self.name = name
        self.display_name = display_name
        self.description = description
        self.category = category
        self.input_schema = input_schema or {}
        self.output_schema = output_schema or {}
        self.config_schema = config_schema or {}
        self.required_permissions = required_permissions or []
        self.confidence_threshold = confidence_threshold


# ── COMMUNICATION SKILLS ──────────────────────────────────────────
SKILL_REGISTRY: dict[str, SkillDef] = {
    # Communication
    "customer_reply": SkillDef(
        name="customer_reply",
        display_name="Customer Reply",
        description="Generate and send contextual responses to customer messages",
        category="communication",
        input_schema={"message": "str", "context": "list", "knowledge": "list"},
        output_schema={"response": "str", "confidence": "float"},
        required_permissions=["send_message"],
    ),
    "summarize_message": SkillDef(
        name="summarize_message",
        display_name="Summarization",
        description="Generate concise summaries of long messages or conversations",
        category="communication",
        input_schema={"text": "str", "max_length": "int"},
        output_schema={"summary": "str"},
    ),
    "translate_message": SkillDef(
        name="translate_message",
        display_name="Translation",
        description="Translate messages between languages",
        category="communication",
        input_schema={"text": "str", "target_language": "str"},
        output_schema={"translated_text": "str", "source_language": "str"},
    ),
    "detect_sentiment": SkillDef(
        name="detect_sentiment",
        display_name="Sentiment Detection",
        description="Analyze message sentiment (positive, negative, neutral)",
        category="communication",
        input_schema={"text": "str"},
        output_schema={"sentiment": "str", "confidence": "float"},
    ),
    "detect_intent": SkillDef(
        name="detect_intent",
        display_name="Intent Detection",
        description="Classify the intent of a customer message",
        category="communication",
        input_schema={"text": "str", "available_intents": "list"},
        output_schema={"intent": "str", "confidence": "float", "entities": "dict"},
    ),
    "escalate_to_human": SkillDef(
        name="escalate_to_human",
        display_name="Escalation",
        description="Escalate conversation to a human agent when AI confidence is low",
        category="communication",
        input_schema={"reason": "str", "conversation_id": "str", "context": "dict"},
        output_schema={"escalated": "bool", "assigned_to": "str"},
        required_permissions=["escalate"],
    ),
    "request_confirmation": SkillDef(
        name="request_confirmation",
        display_name="Request Confirmation",
        description="Ask the customer to confirm an action before proceeding",
        category="communication",
        input_schema={"question": "str", "options": "list"},
        output_schema={"confirmed": "bool", "selected_option": "str"},
    ),
    "send_whatsapp": SkillDef(
        name="send_whatsapp",
        display_name="Send WhatsApp",
        description="Send a message via WhatsApp channel",
        category="communication",
        input_schema={"recipient": "str", "text": "str", "media_url": "str"},
        output_schema={"sent": "bool", "message_id": "str"},
        required_permissions=["send_whatsapp"],
    ),
    "send_email": SkillDef(
        name="send_email",
        display_name="Send Email",
        description="Send an email via connected email channel",
        category="communication",
        input_schema={"to": "str", "subject": "str", "body": "str"},
        output_schema={"sent": "bool", "message_id": "str"},
        required_permissions=["send_email"],
    ),

    # Email
    "email_classification": SkillDef(
        name="email_classification",
        display_name="Email Classification",
        description="Classify incoming emails by type and importance",
        category="email",
        input_schema={"subject": "str", "body": "str", "sender": "str"},
        output_schema={"category": "str", "importance": "float", "is_spam": "bool"},
    ),
    "email_summary": SkillDef(
        name="email_summary",
        display_name="Email Summary",
        description="Generate a concise summary of email content",
        category="email",
        input_schema={"subject": "str", "body": "str"},
        output_schema={"summary": "str", "key_points": "list"},
    ),
    "email_to_whatsapp": SkillDef(
        name="email_to_whatsapp",
        display_name="Email → WhatsApp Alert",
        description="Forward important emails as WhatsApp notifications",
        category="email",
        input_schema={"email_subject": "str", "email_body": "str", "sender": "str"},
        output_schema={"forwarded": "bool", "message_id": "str"},
        required_permissions=["send_whatsapp", "read_email"],
    ),

    # Finance / Settlement
    "extract_payment": SkillDef(
        name="extract_payment",
        display_name="Payment Extraction",
        description="Extract payment details (amount, currency, recipient, date) from text",
        category="finance",
        input_schema={"text": "str"},
        output_schema={"amount": "float", "currency": "str", "recipient": "str", "date": "str", "confidence": "float"},
        confidence_threshold=85,
    ),
    "match_settlement": SkillDef(
        name="match_settlement",
        display_name="Settlement Matching",
        description="Match a payment confirmation against existing unsettled transactions",
        category="finance",
        input_schema={"text": "str", "unsettled_transactions": "list"},
        output_schema={"matched_transaction_id": "str", "confidence": "float", "action": "str"},
        confidence_threshold=90,
    ),
    "reconcile_transactions": SkillDef(
        name="reconcile_transactions",
        display_name="Reconciliation",
        description="Reconcile transactions and calculate settlement status",
        category="finance",
        input_schema={"date_range": "dict", "workspace_id": "str"},
        output_schema={"total_requested": "float", "total_settled": "float", "total_unsettled": "float", "settlement_rate": "float"},
    ),
    "find_unsettled": SkillDef(
        name="find_unsettled",
        display_name="Find Unsettled",
        description="Find all unsettled transactions for a workspace",
        category="finance",
        input_schema={"workspace_id": "str", "date_range": "dict"},
        output_schema={"transactions": "list", "total_amount": "float", "count": "int"},
    ),
    "generate_report": SkillDef(
        name="generate_report",
        display_name="Financial Reporting",
        description="Generate daily/weekly/monthly settlement reports",
        category="finance",
        input_schema={"report_type": "str", "date_range": "dict", "workspace_id": "str"},
        output_schema={"report": "dict", "summary": "str"},
        required_permissions=["read_transaction"],
    ),
    "create_transaction": SkillDef(
        name="create_transaction",
        display_name="Create Transaction",
        description="Create a new transaction record from extracted payment details",
        category="finance",
        input_schema={"amount": "float", "currency": "str", "recipient": "str", "description": "str"},
        output_schema={"transaction_id": "str", "status": "str"},
        required_permissions=["write_transaction"],
        confidence_threshold=90,
    ),

    # Memory
    "search_memory": SkillDef(
        name="search_memory",
        display_name="Search Memory",
        description="Search workspace memory for relevant past context",
        category="memory",
        input_schema={"query": "str", "workspace_id": "str", "memory_type": "str"},
        output_schema={"results": "list", "count": "int"},
    ),
    "save_memory": SkillDef(
        name="save_memory",
        display_name="Save Memory",
        description="Store information in workspace long-term memory",
        category="memory",
        input_schema={"content": "str", "memory_type": "str", "workspace_id": "str", "source": "str"},
        output_schema={"memory_id": "str", "stored": "bool"},
    ),

    # Knowledge
    "search_knowledge": SkillDef(
        name="search_knowledge",
        display_name="Knowledge Search",
        description="Search workspace knowledge base (FAQs, policies, documents)",
        category="knowledge",
        input_schema={"query": "str", "workspace_id": "str"},
        output_schema={"results": "list", "count": "int"},
    ),

    # Operations
    "extract_task": SkillDef(
        name="extract_task",
        display_name="Task Extraction",
        description="Extract actionable tasks from messages",
        category="operations",
        input_schema={"text": "str"},
        output_schema={"tasks": "list", "count": "int"},
    ),
    "detect_reminder": SkillDef(
        name="detect_reminder",
        display_name="Reminder Detection",
        description="Detect and schedule reminders from messages",
        category="operations",
        input_schema={"text": "str", "current_time": "str"},
        output_schema={"has_reminder": "bool", "reminder_time": "str", "reminder_text": "str"},
    ),
}


def get_skill_definition(name: str) -> SkillDef | None:
    return SKILL_REGISTRY.get(name)


def list_skills_by_category() -> dict[str, list[SkillDef]]:
    categories: dict[str, list[SkillDef]] = {}
    for skill in SKILL_REGISTRY.values():
        categories.setdefault(skill.category, []).append(skill)
    return categories
