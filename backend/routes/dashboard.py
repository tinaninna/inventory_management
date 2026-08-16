from fastapi import APIRouter

from backend.database import get_connection

router = APIRouter()


@router.get("/api/dashboard")
def get_dashboard():
    """Return only metrics that can be derived from the imported BOM data."""
    connection = get_connection()
    component_count = connection.execute("SELECT COUNT(*) FROM components").fetchone()[0]
    project_count = connection.execute("SELECT COUNT(*) FROM projects").fetchone()[0]
    bom_item_count = connection.execute("SELECT COUNT(*) FROM bom_items").fetchone()[0]
    projects = connection.execute(
        """
        SELECT projects.id, projects.name, COUNT(bom_items.id) AS component_count,
               COALESCE(SUM(bom_items.quantity_required), 0) AS total_quantity_required
        FROM projects LEFT JOIN bom_items ON bom_items.project_id = projects.id
        GROUP BY projects.id, projects.name ORDER BY projects.name
        """
    ).fetchall()
    connection.close()
    return {
        "component_count": component_count,
        "project_count": project_count,
        "bom_item_count": bom_item_count,
        "projects": [dict(project) for project in projects],
    }