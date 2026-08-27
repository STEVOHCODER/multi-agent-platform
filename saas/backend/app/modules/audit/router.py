from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.modules.core.database import get_db
from app.modules.auth.models import User
from app.modules.auth.service import get_current_user
from app.modules.workspace.models import WorkspaceMember
from app.modules.audit.models import AuditLog, AgentRun
from app.modules.audit.schemas import AuditLogResponse, AgentRunResponse

router = APIRouter(prefix="/api/audit", tags=["audit"])


def _check_workspace(workspace_id: str, user: User, db: Session):
    member = db.query(WorkspaceMember).filter(
        WorkspaceMember.workspace_id == workspace_id,
        WorkspaceMember.user_id == user.id,
        WorkspaceMember.is_active == True,
    ).first()
    if not member:
        from fastapi import HTTPException
        raise HTTPException(status_code=403, detail="Not a member of this workspace")
    return member


@router.get("/workspace/{workspace_id}/logs", response_model=list[AuditLogResponse])
def list_audit_logs(
    workspace_id: str,
    agent_id: str = None,
    action: str = None,
    limit: int = 100,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _check_workspace(workspace_id, user, db)
    q = db.query(AuditLog).filter(AuditLog.workspace_id == workspace_id)
    if agent_id:
        q = q.filter(AuditLog.agent_id == agent_id)
    if action:
        q = q.filter(AuditLog.action == action)
    logs = q.order_by(AuditLog.created_at.desc()).limit(limit).all()
    return [AuditLogResponse.model_validate(l) for l in logs]


@router.get("/workspace/{workspace_id}/runs", response_model=list[AgentRunResponse])
def list_agent_runs(
    workspace_id: str,
    agent_id: str = None,
    limit: int = 100,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _check_workspace(workspace_id, user, db)
    q = db.query(AgentRun).filter(AgentRun.workspace_id == workspace_id)
    if agent_id:
        q = q.filter(AgentRun.agent_id == agent_id)
    runs = q.order_by(AgentRun.created_at.desc()).limit(limit).all()
    return [AgentRunResponse.model_validate(r) for r in runs]
