from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.db import get_db
from backend.models_sqlalchemy import Component, Project, ProjectBomItem

router = APIRouter()


@router.get("/api/dashboard")
def get_dashboard(db: Session = Depends(get_db)):
    """Return catalog and BOM metrics from the MariaDB source of truth."""
    component_count = db.scalar(select(func.count()).select_from(Component)) or 0
    project_count = db.scalar(select(func.count()).select_from(Project)) or 0
    bom_item_count = db.scalar(select(func.count()).select_from(ProjectBomItem)) or 0
    projects = db.execute(
        select(
            Project.id,
            Project.name,
            func.count(ProjectBomItem.id).label("component_count"),
            func.coalesce(func.sum(ProjectBomItem.quantity_required), 0).label("total_quantity_required"),
        )
        .outerjoin(ProjectBomItem, ProjectBomItem.project_id == Project.id)
        .group_by(Project.id, Project.name)
        .order_by(Project.name)
    ).mappings().all()
    return {
        "component_count": component_count,
        "project_count": project_count,
        "bom_item_count": bom_item_count,
        "projects": list(projects),
    }