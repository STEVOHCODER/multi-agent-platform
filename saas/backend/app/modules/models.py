"""All database models for the multi-agent platform.
Import this file to register every table with SQLAlchemy Base."""
from app.modules.workspace.models import Workspace, WorkspaceMember
from app.modules.agent.models import Agent, AgentSkillLink
from app.modules.skill.models import Skill
from app.modules.conversation.models import (
    Channel, Contact, Conversation, UniversalMessage, ConversationMemory,
)
from app.modules.settlement.models import Transaction, TransactionEvent
from app.modules.knowledge.models import KnowledgeSource
from app.modules.audit.models import AuditLog, AgentRun, ToolCall
from app.modules.messaging.models import (
    EmailConnection, WhatsAppConnection, ForwardingRule, MessageLog, Usage,
)

__all__ = [
    "Workspace", "WorkspaceMember",
    "Agent", "AgentSkillLink", "Skill",
    "Channel", "Contact", "Conversation", "UniversalMessage", "ConversationMemory",
    "Transaction", "TransactionEvent",
    "KnowledgeSource",
    "AuditLog", "AgentRun", "ToolCall",
    "EmailConnection", "WhatsAppConnection", "ForwardingRule", "MessageLog", "Usage",
]
