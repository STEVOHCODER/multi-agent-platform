"""In-process event bus for decoupled module communication."""
import asyncio
import logging
from typing import Callable, Any
from dataclasses import dataclass, field

logger = logging.getLogger("mailpilot.events")


@dataclass
class Event:
    name: str
    data: dict = field(default_factory=dict)
    workspace_id: str = ""
    source: str = ""


class EventBus:
    """Simple async event bus. Agents subscribe to events by name."""

    def __init__(self):
        self._handlers: dict[str, list[Callable]] = {}

    def subscribe(self, event_name: str, handler: Callable):
        self._handlers.setdefault(event_name, []).append(handler)
        logger.debug(f"Subscribed {handler.__name__} to {event_name}")

    def unsubscribe(self, event_name: str, handler: Callable):
        if event_name in self._handlers:
            self._handlers[event_name] = [h for h in self._handlers[event_name] if h != handler]

    async def publish(self, event: Event):
        handlers = self._handlers.get(event.name, [])
        if not handlers:
            logger.debug(f"No handlers for event: {event.name}")
            return

        logger.info(f"Publishing event: {event.name} (workspace={event.workspace_id})")
        for handler in handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(event)
                else:
                    handler(event)
            except Exception as e:
                logger.error(f"Error in event handler {handler.__name__} for {event.name}: {e}")


# Global event bus instance
event_bus = EventBus()


# ── Event name constants ──────────────────────────────────────────
class Events:
    # Channel events
    WHATSAPP_MESSAGE_RECEIVED = "whatsapp.message_received"
    EMAIL_RECEIVED = "email.received"

    # Agent events
    AGENT_MESSAGE_RECEIVED = "agent.message_received"
    AGENT_RESPONSE_REQUIRED = "agent.response_required"
    AGENT_RESPONSE_SENT = "agent.response_sent"
    AGENT_ESCALATED = "agent.escalated"

    # Transaction events
    TRANSACTION_CREATED = "transaction.created"
    TRANSACTION_SETTLED = "transaction.settled"
    TRANSACTION_NEEDS_REVIEW = "transaction.needs_review"
    TRANSACTION_CANCELLED = "transaction.cancelled"

    # System events
    WORKSPACE_CREATED = "workspace.created"
    AGENT_CREATED = "agent.created"
    SKILL_EXECUTED = "skill.executed"
