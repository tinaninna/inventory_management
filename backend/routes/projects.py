from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.db import get_db
from backend.models import Project
from backend.models_sqlalchemy import Project as ProjectRecord, ProjectBuild
from backend.project_consumption import (
    BuildShortageError,
    BuildValidationError,
    ProjectNotFoundError,
    consume_project,
)
from backend.schemas import BuildHistoryItem, BuildRequest, BuildResponse

router = APIRouter()


@router.get("/api/projects", response_model=list[Project])
def get_projects(db: Session = Depends(get_db)):
    return db.execute(
        select(ProjectRecord.id, ProjectRecord.name).order_by(ProjectRecord.id)
    ).mappings().all()


@router.post("/api/projects/{project_id}/build", response_model=BuildResponse)
def build_project(project_id: int, request: BuildRequest, db: Session = Depends(get_db)):
    try:
        return consume_project(db, project_id, request.quantity)
    except ProjectNotFoundError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error
    except BuildShortageError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "project": {"id": error.project_id, "name": error.project_name},
                "build_quantity": error.build_quantity,
                "success": False,
                "build_id": None,
                "required_components": [line.__dict__ for line in error.lines],
                "shortages": [line.__dict__ for line in error.lines if line.shortage_quantity > 0],
            },
        ) from error
    except BuildValidationError as error:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(error)) from error


@router.get("/api/projects/{project_id}/builds", response_model=list[BuildHistoryItem])
def get_project_builds(project_id: int, db: Session = Depends(get_db)):
    if db.get(ProjectRecord, project_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    builds = db.scalars(
        select(ProjectBuild)
        .where(ProjectBuild.project_id == project_id)
        .order_by(ProjectBuild.id.desc())
    ).all()
    return builds