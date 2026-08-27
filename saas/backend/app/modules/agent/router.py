from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.modules.core.database import get_db
from app.modules.auth.models import User
from app.modules.auth.service import get_current_user
from app.modules.workspace.models import WorkspaceMember
from app.modules.agent.models import Agent, AgentSkillLink
from app.modules.agent.schemas import AgentCreate, AgentUpdate, AgentResponse, AgentTemplateResponse
from app.modules.agent.templates import AGENT_TEMPLATES
from app.modules.skill.models import Skill

router = APIRouter(prefix="/api/agents", tags=["agents"])


def _check_workspace_access(workspace_id: str, user: User, db: Session):
    member = db.query(WorkspaceMember).filter(
        WorkspaceMember.workspace_id == workspace_id,
        WorkspaceMember.user_id == user.id,
        WorkspaceMember.is_active == True,
    ).first()
    if not member:
        raise HTTPException(status_code=403, detail="Not a member of this workspace")
    return member


@router.get("/templates", response_model=list[AgentTemplateResponse])
def list_templates():
    """List all available agent templates."""
    return [
        AgentTemplateResponse(
            id=t.id, name=t.name, description=t.description,
            model=t.model, skills=t.skills, channels=t.channels,
            response_mode=t.response_mode,
        )
        for t in AGENT_TEMPLATES.values()
    ]


@router.post("/workspace/{workspace_id}", response_model=AgentResponse)
def create_agent(
    workspace_id: str,
    data: AgentCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _check_workspace_access(workspace_id, user, db)

    agent = Agent(
        workspace_id=workspace_id,
        name=data.name,
        description=data.description,
        model=data.model,
        system_instructions=data.system_instructions,
        response_mode=data.response_mode,
        auto_reply=data.auto_reply,
        memory_enabled=data.memory_enabled,
        channels=data.channels,
        confidence_threshold=data.confidence_threshold,
        simulation_mode=data.simulation_mode,
    )
    db.add(agent)
    db.flush()

    # Attach skills
    for skill_name in data.skills:
        skill = db.query(Skill).filter(Skill.name == skill_name).first()
        if skill:
            link = AgentSkillLink(agent_id=agent.id, skill_id=skill.id)
            db.add(link)

    db.commit()
    db.refresh(agent)
    return AgentResponse.model_validate(agent)


@router.post("/workspace/{workspace_id}/from-template/{template_id}", response_model=AgentResponse)
def create_agent_from_template(
    workspace_id: str,
    template_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _check_workspace_access(workspace_id, user, db)

    template = AGENT_TEMPLATES.get(template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    agent = Agent(
        workspace_id=workspace_id,
        template_id=template_id,
        name=template.name,
        description=template.description,
        model=template.model,
        system_instructions=template.system_instructions,
        response_mode=template.response_mode,
        auto_reply=template.auto_reply,
        memory_enabled=template.memory_enabled,
        channels=template.channels,
    )
    db.add(agent)
    db.flush()

    # Auto-attach template skills
    for skill_name in template.skills:
        skill = db.query(Skill).filter(Skill.name == skill_name).first()
        if skill:
            link = AgentSkillLink(agent_id=agent.id, skill_id=skill.id)
            db.add(link)

    db.commit()
    db.refresh(agent)
    return AgentResponse.model_validate(agent)


@router.get("/workspace/{workspace_id}", response_model=list[AgentResponse])
def list_agents(
    workspace_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _check_workspace_access(workspace_id, user, db)
    agents = db.query(Agent).filter(Agent.workspace_id == workspace_id).all()
    return [AgentResponse.model_validate(a) for a in agents]


@router.get("/{agent_id}", response_model=AgentResponse)
def get_agent(
    agent_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    _check_workspace_access(agent.workspace_id, user, db)
    return AgentResponse.model_validate(agent)


@router.put("/{agent_id}", response_model=AgentResponse)
def update_agent(
    agent_id: str,
    data: AgentUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    _check_workspace_access(agent.workspace_id, user, db)

    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(agent, k, v)
    db.commit()
    db.refresh(agent)
    return AgentResponse.model_validate(agent)


@router.delete("/{agent_id}")
def delete_agent(
    agent_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    _check_workspace_access(agent.workspace_id, user, db)
    db.delete(agent)
    db.commit()
    return {"ok": True}


@router.post("/{agent_id}/skills/{skill_name}")
def add_skill_to_agent(
    agent_id: str,
    skill_name: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    _check_workspace_access(agent.workspace_id, user, db)

    skill = db.query(Skill).filter(Skill.name == skill_name).first()
    if not skill:
        raise HTTPException(status_code=404, detail="Skill not found")

    existing = db.query(AgentSkillLink).filter(
        AgentSkillLink.agent_id == agent_id, AgentSkillLink.skill_id == skill.id
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Skill already attached")

    link = AgentSkillLink(agent_id=agent_id, skill_id=skill.id)
    db.add(link)
    db.commit()
    return {"ok": True}


@router.delete("/{agent_id}/skills/{skill_name}")
def remove_skill_from_agent(
    agent_id: str,
    skill_name: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    _check_workspace_access(agent.workspace_id, user, db)

    skill = db.query(Skill).filter(Skill.name == skill_name).first()
    if not skill:
        raise HTTPException(status_code=404, detail="Skill not found")

    link = db.query(AgentSkillLink).filter(
        AgentSkillLink.agent_id == agent_id, AgentSkillLink.skill_id == skill.id
    ).first()
    if link:
        db.delete(link)
        db.commit()
    return {"ok": True}
