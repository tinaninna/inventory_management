from fastapi import APIRouter, HTTPException
from backend.database import get_connection
from backend.models import BOMItem

router = APIRouter()


@router.get("/api/projects/{project_id}/bom", response_model=list[BOMItem])
def get_project_bom(project_id: int):
    connection = get_connection()

    project = connection.execute(
        "SELECT id FROM projects WHERE id = ?",
        (project_id,)
    ).fetchone()

    if project is None:
        connection.close()
        raise HTTPException(status_code=404, detail="Project not found")

    bom = connection.execute(
        """
        SELECT
            bom_items.id,
            components.id AS component_id,
            components.manufacturer_part_number,
            components.description,
            components.value,
            components.manufacturer,
            bom_items.quantity_required,
            bom_items.reference_designators
        FROM bom_items
        JOIN components
            ON bom_items.component_id = components.id
        WHERE bom_items.project_id = ?
        ORDER BY components.id
        """,
        (project_id,)
    ).fetchall()

    connection.close()

    return [dict(item) for item in bom]