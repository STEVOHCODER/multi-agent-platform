from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.modules.core.database import get_db
from app.modules.auth.models import User
from app.modules.auth.service import get_current_user
from app.modules.skill.models import Skill
from app.modules.skill.registry import SKILL_REGISTRY, list_skills_by_category
from app.modules.skill.schemas import SkillResponse, SkillDefinitionResponse

router = APIRouter(prefix="/api/skills", tags=["skills"])


@router.get("/registry", response_model=list[SkillDefinitionResponse])
def list_skill_definitions():
    """List all available skill definitions from the global registry."""
    return [
        SkillDefinitionResponse(
            name=s.name,
            display_name=s.display_name,
            description=s.description,
            category=s.category,
            input_schema=s.input_schema,
            output_schema=s.output_schema,
            required_permissions=s.required_permissions,
            confidence_threshold=s.confidence_threshold,
        )
        for s in SKILL_REGISTRY.values()
    ]


@router.get("/registry/{category}")
def list_skills_by_category(category: str):
    """List skill definitions grouped by category."""
    all_cats = list_skills_by_category()
    if category in all_cats:
        return {category: [
            {"name": s.name, "display_name": s.display_name, "description": s.description}
            for s in all_cats[category]
        ]}
    return {"error": "Category not found"}


@router.get("/workspace/{workspace_id}", response_model=list[SkillResponse])
def list_workspace_skills(
    workspace_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List skills available in a workspace."""
    skills = db.query(Skill).filter(Skill.is_enabled == True).all()
    return [SkillResponse.model_validate(s) for s in skills]
