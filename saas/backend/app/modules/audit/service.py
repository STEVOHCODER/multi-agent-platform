"""Audit logging service — records agent actions for explainability."""
from sqlalchemy.orm import Session
from app.modules.audit.models import AuditLog, AgentRun, ToolCall


def log_audit(
    db: Session,
    workspace_id: str,
    action: str,
    agent_id: str = None,
    conversation_id: str = None,
    skill_name: str = None,
    parameters: dict = None,
    result: dict = None,
    confidence: float = None,
    actor_type: str = "agent",
    actor_id: str = None,
) -> AuditLog:
    entry = AuditLog(
        workspace_id=workspace_id,
        agent_id=agent_id,
        conversation_id=conversation_id,
        action=action,
        skill_name=skill_name,
        parameters=parameters or {},
        result=result or {},
        confidence=confidence,
        actor_type=actor_type,
        actor_id=actor_id,
    )
    db.add(entry)
    db.flush()
    return entry


def record_agent_run(
    db: Session,
    workspace_id: str,
    agent_id: str,
    input_text: str = "",
    intent_detected: str = None,
    intent_confidence: float = None,
    skills_called: list = None,
    output_text: str = "",
    status: str = "completed",
    error: str = None,
    conversation_id: str = None,
    message_id: str = None,
    duration_ms: int = None,
) -> AgentRun:
    run = AgentRun(
        workspace_id=workspace_id,
        agent_id=agent_id,
        conversation_id=conversation_id,
        message_id=message_id,
        input_text=input_text,
        intent_detected=intent_detected,
        intent_confidence=intent_confidence,
        skills_called=skills_called or [],
        output_text=output_text,
        status=status,
        error=error,
        duration_ms=duration_ms,
    )
    db.add(run)
    db.flush()
    return run


def record_tool_call(
    db: Session,
    agent_run_id: str,
    skill_name: str,
    input_params: dict = None,
    output_result: dict = None,
    confidence: float = None,
    status: str = "success",
    duration_ms: int = None,
) -> ToolCall:
    tc = ToolCall(
        agent_run_id=agent_run_id,
        skill_name=skill_name,
        input_params=input_params or {},
        output_result=output_result or {},
        confidence=confidence,
        status=status,
        duration_ms=duration_ms,
    )
    db.add(tc)
    db.flush()
    return tc
