from fastapi import APIRouter
from backend.database import get_connection
from backend.models import Component

router = APIRouter()


@router.get("/api/components", response_model=list[Component])
def get_components():
    connection = get_connection()

    components = connection.execute(
        """
        SELECT
            id,
            manufacturer_part_number,
            description,
            value,
            manufacturer
        FROM components
        ORDER BY id
        """
    ).fetchall()

    connection.close()

    return [dict(component) for component in components]