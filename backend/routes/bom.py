from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from backend.db import get_db
from backend.models import BOMItem
from backend.models_sqlalchemy import Project as ProjectRecord, ProjectBomItem

router = APIRouter()


@router.get("/api/projects/{project_id}/bom", response_model=list[BOMItem])
def get_project_bom(project_id: int, db: Session = Depends(get_db)):
    if db.get(ProjectRecord, project_id) is None:
        raise HTTPException(status_code=404, detail="Project not found")
    items = db.scalars(
        select(ProjectBomItem)
        .options(joinedload(ProjectBomItem.component))
        .where(ProjectBomItem.project_id == project_id)
        .order_by(ProjectBomItem.component_id)
    ).unique().all()
    return [
        {
            "id": item.id,
            "component_id": item.component_id,
            "manufacturer_part_number": item.component.manufacturer_part_number,
            "description": item.component.description,
            "value": item.component.value,
            "manufacturer": item.component.manufacturer,
            "quantity_required": item.quantity_required,
            "reference_designators": item.reference_designators,
        }
        for item in items
    ]