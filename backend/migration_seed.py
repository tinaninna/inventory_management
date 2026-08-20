from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.db import SessionLocal
from backend.inventory_import import normalize_part_number
from backend.models_sqlalchemy import Component, Project, ProjectBomItem


@dataclass(frozen=True)
class UnmatchedBomItem:
    source_bom_id: int
    source_project_id: int
    project_name: str
    source_component_id: int
    manufacturer_part_number: str


class MigrationSeedError(RuntimeError):
    def __init__(self, unmatched_bom_items: list[UnmatchedBomItem]):
        self.unmatched_bom_items = unmatched_bom_items
        super().__init__(
            f"Cannot migrate {len(unmatched_bom_items)} BOM items because their "
            "components are not present in MariaDB."
        )


def migrate_existing_sqlite_data(
    db: Session | None = None,
    sqlite_path: Path | None = None,
    *,
    strict: bool = True,
) -> dict[str, object]:
    """Copy SQLite projects and BOM relationships into MariaDB without changing SQLite."""
    sqlite_path = sqlite_path or Path(__file__).resolve().parent.parent / "data" / "inventory.db"
    if not sqlite_path.exists():
        raise FileNotFoundError(f"SQLite database not found at {sqlite_path}")

    owns_session = db is None
    db = db or SessionLocal()
    try:
        with sqlite3.connect(sqlite_path) as sqlite_conn:
            sqlite_conn.row_factory = sqlite3.Row
            component_rows = sqlite_conn.execute(
                "SELECT id, manufacturer_part_number, description, value, manufacturer FROM components ORDER BY id"
            ).fetchall()
            project_rows = sqlite_conn.execute(
                "SELECT id, name FROM projects ORDER BY id"
            ).fetchall()
            bom_rows = sqlite_conn.execute(
                """
                SELECT b.id, b.project_id, p.name AS project_name, b.component_id,
                       c.manufacturer_part_number, b.quantity_required,
                       b.reference_designators
                FROM bom_items b
                JOIN projects p ON p.id = b.project_id
                JOIN components c ON c.id = b.component_id
                ORDER BY b.id
                """
            ).fetchall()

        components_by_part: dict[str, Component] = {}
        ambiguous_parts: set[str] = set()
        for component in db.scalars(select(Component)).all():
            normalized = normalize_part_number(component.manufacturer_part_number)
            if normalized in components_by_part:
                ambiguous_parts.add(normalized)
            components_by_part[normalized] = component

        components_created = 0
        for row in component_rows:
            normalized = normalize_part_number(row["manufacturer_part_number"])
            if normalized in ambiguous_parts:
                continue
            if normalized in components_by_part:
                continue
            component = Component(
                manufacturer_part_number=row["manufacturer_part_number"],
                description=row["description"],
                value=row["value"],
                manufacturer=row["manufacturer"],
            )
            db.add(component)
            db.flush()
            components_by_part[normalized] = component
            components_created += 1

        unmatched: list[UnmatchedBomItem] = []
        resolved_bom: list[tuple[sqlite3.Row, Component]] = []
        for row in bom_rows:
            normalized = normalize_part_number(row["manufacturer_part_number"])
            component = components_by_part.get(normalized)
            if component is None or normalized in ambiguous_parts:
                unmatched.append(UnmatchedBomItem(
                    source_bom_id=row["id"],
                    source_project_id=row["project_id"],
                    project_name=row["project_name"],
                    source_component_id=row["component_id"],
                    manufacturer_part_number=row["manufacturer_part_number"],
                ))
            else:
                resolved_bom.append((row, component))

        if unmatched and strict:
            raise MigrationSeedError(unmatched)

        projects_migrated = 0
        for row in project_rows:
            project = db.get(Project, row["id"])
            if project is None:
                db.add(Project(id=row["id"], name=row["name"]))
                projects_migrated += 1
            elif project.name != row["name"]:
                raise ValueError(
                    f"MariaDB project id {row['id']} is named {project.name!r}, "
                    f"but SQLite contains {row['name']!r}."
                )

        bom_items_migrated = 0
        existing_bom = {
            (item.project_id, item.component_id): item
            for item in db.scalars(select(ProjectBomItem)).all()
        }
        for row, component in resolved_bom:
            key = (row["project_id"], component.id)
            item = existing_bom.get(key)
            if item is None:
                db.add(ProjectBomItem(
                    id=row["id"],
                    project_id=row["project_id"],
                    component_id=component.id,
                    quantity_required=row["quantity_required"],
                    reference_designators=row["reference_designators"],
                ))
                bom_items_migrated += 1
            elif (
                item.quantity_required != row["quantity_required"]
                or item.reference_designators != row["reference_designators"]
            ):
                raise ValueError(f"MariaDB BOM item {item.id} conflicts with SQLite BOM item {row['id']}.")

        db.commit()
        return {
            "source_components": len(component_rows),
            "components_created": components_created,
            "projects": projects_migrated,
            "bom_items": bom_items_migrated,
            "unmatched_bom_items": unmatched,
        }
    except Exception:
        db.rollback()
        raise
    finally:
        if owns_session:
            db.close()
