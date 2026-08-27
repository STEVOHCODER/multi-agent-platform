"""Agent Router — the brain. Routes messages to agents, executes skills, produces responses."""
import json
import logging
import time
from sqlalchemy.orm import Session

from app.modules.ai_engine import get_provider
from app.modules.agent.models import Agent, AgentSkillLink
from app.modules.skill.models import Skill
from app.modules.skill.registry import get_skill_definition, SKILL_REGISTRY
from app.modules.conversation.models import Conversation, UniversalMessage, ConversationMemory
from app.modules.audit.service import record_agent_run, record_tool_call, log_audit
from app.modules.settlement.service import create_transaction, match_and_settle, find_unsettled, generate_daily_report
from app.modules.knowledge.models import KnowledgeSource
from app.modules.conversation.models import Channel

logger = logging.getLogger("mailpilot.router")


async def route_message(db: Session, message: UniversalMessage) -> dict:
    """
    Route an incoming message to the appropriate agent.
    Returns: {"agent_id": str, "response": str, "skill_used": str, "confidence": float}
    """
    workspace_id = message.workspace_id
    start_time = time.time()

    # Find agents assigned to this channel
    agents = db.query(Agent).filter(
        Agent.workspace_id == workspace_id,
        Agent.status == "active",
    ).all()

    if not agents:
        return {"agent_id": None, "response": "", "skill_used": None, "confidence": 0.0}

    # Filter agents that listen on this channel
    channel_agents = [
        a for a in agents
        if message.channel in (a.channels or [])
    ]

    if not channel_agents:
        # Fall back to any active agent
        channel_agents = agents

    # For now: pick the first matching agent (can be enhanced with intent routing later)
    agent = channel_agents[0]

    # Process through the agent
    result = await process_agent_message(db, agent, message)

    elapsed_ms = int((time.time() - start_time) * 1000)

    # Record the run
    run = record_agent_run(
        db,
        workspace_id=workspace_id,
        agent_id=agent.id,
        input_text=message.text or "",
        intent_detected=result.get("intent"),
        intent_confidence=result.get("intent_confidence"),
        skills_called=[result.get("skill_used")] if result.get("skill_used") else [],
        output_text=result.get("response", ""),
        status="completed" if result.get("response") else "no_response",
        conversation_id=message.conversation_id,
        message_id=message.id,
        duration_ms=elapsed_ms,
    )
    db.commit()

    return {
        "agent_id": agent.id,
        "response": result.get("response", ""),
        "skill_used": result.get("skill_used"),
        "confidence": result.get("confidence", 0.0),
        "intent": result.get("intent"),
        "run_id": run.id,
    }


async def process_agent_message(db: Session, agent: Agent, message: UniversalMessage) -> dict:
    """Process a message through a specific agent using its skills."""

    # Get agent's skills
    skill_links = db.query(AgentSkillLink).filter(
        AgentSkillLink.agent_id == agent.id,
        AgentSkillLink.is_enabled == True,
    ).all()

    skill_names = []
    for link in skill_links:
        skill = db.query(Skill).filter(Skill.id == link.skill_id).first()
        if skill:
            skill_names.append(skill.name)

    # Build context
    context = _build_context(db, agent, message)

    # Use AI to determine intent and select skills
    provider = get_provider()

    # Build tool definitions from skills
    tools = _build_tool_definitions(skill_names)

    # Build messages for AI
    ai_messages = [{"role": "user", "content": message.text or ""}]

    system_prompt = agent.system_instructions or "You are a helpful AI assistant."
    system_prompt += f"\n\nAvailable skills: {', '.join(skill_names)}"
    system_prompt += "\n\nUse the provided tools/skills to handle the user's request."

    try:
        result = await provider.chat(
            messages=ai_messages,
            model=agent.model,
            system_prompt=system_prompt,
            tools=tools if tools else None,
        )
    except Exception as e:
        logger.error(f"AI provider error: {e}")
        return {"response": "I'm experiencing technical difficulties. Please try again.", "confidence": 0.0}

    # Process tool calls if any
    content = result.get("content", "")
    tool_calls = result.get("tool_calls", [])

    if tool_calls:
        skill_results = []
        for tc in tool_calls:
            func_name = tc.get("function", {}).get("name", "")
            func_args = {}
            try:
                func_args = json.loads(tc.get("function", {}).get("arguments", "{}"))
            except json.JSONDecodeError:
                pass

            skill_result = await execute_skill(db, agent, func_name, func_args, message)
            skill_results.append({"skill": func_name, "result": skill_result})

            # Record tool call
            record_tool_call(
                db,
                agent_run_id=None,  # Will be set after run is created
                skill_name=func_name,
                input_params=func_args,
                output_result=skill_result,
                confidence=skill_result.get("confidence", 0.0),
            )

        # Let AI synthesize the final response
        if skill_results:
            synthesis_messages = [
                {"role": "user", "content": message.text or ""},
                {"role": "assistant", "content": content},
                {"role": "user", "content": f"Tool results: {json.dumps(skill_results)}. Synthesize a final response."},
            ]
            try:
                synthesis = await provider.chat(
                    messages=synthesis_messages,
                    model=agent.model,
                    system_prompt=system_prompt,
                )
                content = synthesis.get("content", content)
            except Exception:
                pass

        return {
            "response": content,
            "skill_used": skill_results[0]["skill"] if skill_results else None,
            "confidence": _avg_confidence(skill_results),
            "intent": tool_calls[0].get("function", {}).get("name") if tool_calls else None,
        }

    return {
        "response": content,
        "skill_used": None,
        "confidence": 0.5,
        "intent": None,
    }


def _build_context(db: Session, agent: Agent, message: UniversalMessage) -> str:
    """Build context string from workspace memory and knowledge."""
    parts = []

    # Get recent conversation messages
    recent = db.query(UniversalMessage).filter(
        UniversalMessage.conversation_id == message.conversation_id,
    ).order_by(UniversalMessage.created_at.desc()).limit(10).all()

    if recent:
        parts.append("Recent conversation:")
        for m in reversed(recent):
            parts.append(f"  {m.sender_name or m.sender_id}: {m.text}")

    # Get workspace memory
    if agent.memory_enabled:
        memories = db.query(ConversationMemory).filter(
            ConversationMemory.workspace_id == agent.workspace_id,
        ).order_by(ConversationMemory.created_at.desc()).limit(20).all()
        if memories:
            parts.append("Workspace memory:")
            for mem in memories:
                parts.append(f"  [{mem.category}] {mem.content}")

    # Get knowledge base
    knowledge = db.query(KnowledgeSource).filter(
        KnowledgeSource.workspace_id == agent.workspace_id,
        KnowledgeSource.is_active == True,
    ).limit(10).all()
    if knowledge:
        parts.append("Knowledge base:")
        for k in knowledge:
            parts.append(f"  [{k.category}] {k.title}: {k.content[:200]}")

    return "\n".join(parts)


def _build_tool_definitions(skill_names: list[str]) -> list[dict]:
    """Convert skill names to OpenAI-compatible tool definitions."""
    tools = []
    for name in skill_names:
        skill_def = get_skill_definition(name)
        if not skill_def:
            continue

        # Convert simple type annotations to JSON Schema types
        properties = {}
        for param_name, param_type in skill_def.input_schema.items():
            json_type = "string"  # default
            if param_type == "float":
                json_type = "number"
            elif param_type == "int":
                json_type = "integer"
            elif param_type == "bool":
                json_type = "boolean"
            elif param_type == "list":
                json_type = "array"
            elif param_type == "dict":
                json_type = "object"
            properties[param_name] = {"type": json_type}

        tools.append({
            "type": "function",
            "function": {
                "name": skill_def.name,
                "description": skill_def.description,
                "parameters": {
                    "type": "object",
                    "properties": properties,
                },
            },
        })
    return tools


async def execute_skill(db: Session, agent: Agent, skill_name: str, args: dict, message: UniversalMessage) -> dict:
    """Execute a specific skill and return results."""

    # Settlement skills
    if skill_name == "create_transaction":
        tx = create_transaction(
            db,
            workspace_id=agent.workspace_id,
            amount=args.get("amount", 0),
            currency=args.get("currency", "USD"),
            recipient=args.get("recipient", ""),
            description=args.get("description", ""),
            confidence=args.get("confidence", 0.5),
            source_message_id=message.id,
            conversation_id=message.conversation_id,
        )
        return {"transaction_id": tx.id, "status": tx.status, "confidence": tx.confidence}

    elif skill_name == "find_unsettled":
        return find_unsettled(db, agent.workspace_id)

    elif skill_name == "match_settlement":
        matches = match_and_settle(db, agent.workspace_id, args.get("text", message.text or ""), args.get("confidence", 0.5))
        return {"matches": matches, "count": len(matches)}

    elif skill_name == "generate_report":
        return generate_daily_report(db, agent.workspace_id)

    elif skill_name == "reconcile_transactions":
        from datetime import datetime, timezone, timedelta
        now = datetime.now(timezone.utc)
        start = now - timedelta(days=args.get("days", 1))
        from app.modules.settlement.service import reconcile_date_range
        return reconcile_date_range(db, agent.workspace_id, start, now)

    # Knowledge/memory skills
    elif skill_name == "search_knowledge":
        query = args.get("query", message.text or "")
        results = db.query(KnowledgeSource).filter(
            KnowledgeSource.workspace_id == agent.workspace_id,
            KnowledgeSource.is_active == True,
            KnowledgeSource.content.contains(query),
        ).limit(5).all()
        return {"results": [{"title": k.title, "content": k.content[:300]} for k in results]}

    elif skill_name == "search_memory":
        query = args.get("query", message.text or "")
        results = db.query(ConversationMemory).filter(
            ConversationMemory.workspace_id == agent.workspace_id,
            ConversationMemory.content.contains(query),
        ).limit(10).all()
        return {"results": [{"content": m.content, "category": m.category} for m in results]}

    elif skill_name == "save_memory":
        mem = ConversationMemory(
            workspace_id=agent.workspace_id,
            conversation_id=message.conversation_id,
            memory_type=args.get("memory_type", "long_term"),
            content=args.get("content", ""),
            source=args.get("source", "observed"),
            confidence=args.get("confidence", 0.5),
            category=args.get("category", ""),
            key=args.get("key", ""),
        )
        db.add(mem)
        db.flush()
        return {"memory_id": mem.id, "stored": True}

    # Communication skills
    elif skill_name == "send_whatsapp":
        channel = db.query(Channel).filter(
            Channel.workspace_id == agent.workspace_id,
            Channel.channel_type == "whatsapp",
            Channel.is_active == True,
        ).first()
        if channel:
            from app.modules.messaging.whatsapp_sender import send_whatsapp_message
            config = channel.config or {}
            result = await send_whatsapp_message(
                phone_number=config.get("phone_number", ""),
                meta_phone_number_id=config.get("meta_phone_number_id", ""),
                meta_access_token=channel.credentials.get("meta_access_token", ""),
                subject=args.get("subject", ""),
                sender=args.get("sender", "AI Agent"),
                body=args.get("text", args.get("body", "")),
                importance=args.get("importance", 0.5),
            )
            return result
        return {"ok": False, "error": "No WhatsApp channel configured"}

    # Default: return args as result
    return {"skill": skill_name, "args": args, "executed": True}


def _avg_confidence(skill_results: list[dict]) -> float:
    if not skill_results:
        return 0.0
    confidences = [r["result"].get("confidence", 0.5) for r in skill_results]
    return sum(confidences) / len(confidences)
