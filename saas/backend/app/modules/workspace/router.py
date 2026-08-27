import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import re

from app.modules.core.database import get_db
from app.modules.auth.models import User
from app.modules.auth.service import get_current_user
from app.modules.workspace.models import Workspace, WorkspaceMember
from app.modules.workspace.schemas import WorkspaceCreate, WorkspaceResponse

router = APIRouter(prefix="/api/workspaces", tags=["workspaces"])


def _slugify(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


@router.post("/", response_model=WorkspaceResponse)
def create_workspace(
    data: WorkspaceCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    slug = _slugify(data.name)
    existing = db.query(Workspace).filter(Workspace.slug == slug).first()
    if existing:
        slug = f"{slug}-{str(uuid.uuid4())[:8]}"

    ws = Workspace(name=data.name, slug=slug, owner_id=user.id)
    db.add(ws)
    db.flush()

    member = WorkspaceMember(workspace_id=ws.id, user_id=user.id, role="owner")
    db.add(member)
    db.commit()
    db.refresh(ws)
    return WorkspaceResponse.model_validate(ws)


@router.get("/", response_model=list[WorkspaceResponse])
def list_workspaces(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    memberships = db.query(WorkspaceMember).filter(WorkspaceMember.user_id == user.id, WorkspaceMember.is_active == True).all()
    ws_ids = [m.workspace_id for m in memberships]
    workspaces = db.query(Workspace).filter(Workspace.id.in_(ws_ids)).all()
    return [WorkspaceResponse.model_validate(w) for w in workspaces]


@router.get("/{workspace_id}", response_model=WorkspaceResponse)
def get_workspace(
    workspace_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    member = db.query(WorkspaceMember).filter(
        WorkspaceMember.workspace_id == workspace_id,
        WorkspaceMember.user_id == user.id,
        WorkspaceMember.is_active == True,
    ).first()
    if not member:
        raise HTTPException(status_code=403, detail="Not a member of this workspace")
    ws = db.query(Workspace).filter(Workspace.id == workspace_id).first()
    if not ws:
        raise HTTPException(status_code=404, detail="Workspace not found")
    return WorkspaceResponse.model_validate(ws)
