from fastapi import APIRouter
from backend.database import get_connection
from backend.models import Project

router = APIRouter()


@router.get("/api/projects", response_model=list[Project])
def get_projects():
    connection = get_connection()

    projects = connection.execute(
        """
        SELECT
            id,
            name
        FROM projects
        ORDER BY id
        """
    ).fetchall()

    connection.close()

    return [dict(project) for project in projects]