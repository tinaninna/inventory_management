from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.db import get_db
from backend.models import Project
from backend.models_sqlalchemy import Project as ProjectRecord

router = APIRouter()


@router.get("/api/projects", response_model=list[Project])
def get_projects(db: Session = Depends(get_db)):
    return db.execute(
        select(ProjectRecord.id, ProjectRecord.name).order_by(ProjectRecord.id)
    ).mappings().all()