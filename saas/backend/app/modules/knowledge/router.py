from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.modules.core.database import get_db
from app.modules.auth.models import User
from app.modules.auth.service import get_current_user
from app.modules.workspace.models import WorkspaceMember
from app.modules.knowledge.models import KnowledgeSource
from app.modules.knowledge.schemas import KnowledgeCreate, KnowledgeUpdate, KnowledgeResponse

router = APIRouter(prefix="/api/knowledge", tags=["knowledge"])


def _check_workspace(workspace_id: str, user: User, db: Session):
    member = db.query(WorkspaceMember).filter(
        WorkspaceMember.workspace_id == workspace_id,
        WorkspaceMember.user_id == user.id,
        WorkspaceMember.is_active == True,
    ).first()
    if not member:
        raise HTTPException(status_code=403, detail="Not a member of this workspace")
    return member


@router.post("/workspace/{workspace_id}", response_model=KnowledgeResponse)
def create_knowledge(
    workspace_id: str,
    data: KnowledgeCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _check_workspace(workspace_id, user, db)
    ks = KnowledgeSource(workspace_id=workspace_id, **data.model_dump())
    db.add(ks)
    db.commit()
    db.refresh(ks)
    return KnowledgeResponse.model_validate(ks)


@router.get("/workspace/{workspace_id}", response_model=list[KnowledgeResponse])
def list_knowledge(
    workspace_id: str,
    category: str = None,
    query: str = None,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _check_workspace(workspace_id, user, db)
    q = db.query(KnowledgeSource).filter(
        KnowledgeSource.workspace_id == workspace_id,
        KnowledgeSource.is_active == True,
    )
    if category:
        q = q.filter(KnowledgeSource.category == category)
    if query:
        q = q.filter(KnowledgeSource.content.contains(query))
    items = q.order_by(KnowledgeSource.created_at.desc()).limit(100).all()
    return [KnowledgeResponse.model_validate(k) for k in items]


@router.put("/workspace/{workspace_id}/{ks_id}", response_model=KnowledgeResponse)
def update_knowledge(
    workspace_id: str,
    ks_id: str,
    data: KnowledgeUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _check_workspace(workspace_id, user, db)
    ks = db.query(KnowledgeSource).filter(KnowledgeSource.id == ks_id, KnowledgeSource.workspace_id == workspace_id).first()
    if not ks:
        raise HTTPException(status_code=404, detail="Knowledge source not found")
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(ks, k, v)
    db.commit()
    db.refresh(ks)
    return KnowledgeResponse.model_validate(ks)


@router.delete("/workspace/{workspace_id}/{ks_id}")
def delete_knowledge(
    workspace_id: str,
    ks_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _check_workspace(workspace_id, user, db)
    ks = db.query(KnowledgeSource).filter(KnowledgeSource.id == ks_id, KnowledgeSource.workspace_id == workspace_id).first()
    if not ks:
        raise HTTPException(status_code=404, detail="Knowledge source not found")
    db.delete(ks)
    db.commit()
    return {"ok": True}
