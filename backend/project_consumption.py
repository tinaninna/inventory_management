from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from backend.models_sqlalchemy import (
    InventoryItem,
    InventoryTransaction,
    InventoryTransactionType,
    Project,
    ProjectBomItem,
    ProjectBuild,
    ProjectBuildItem,
    ProjectBuildStatus,
)


@dataclass(frozen=True)
class BuildLine:
    component_id: int
    manufacturer_part_number: str
    required_quantity: int
    previous_available_quantity: int
    consumed_quantity: int
    remaining_available_quantity: int
    shortage_quantity: int


class BuildValidationError(ValueError):
    pass


class ProjectNotFoundError(BuildValidationError):
    pass


class BuildShortageError(ValueError):
    def __init__(self, project_id: int, project_name: str, build_quantity: int, lines: list[BuildLine]):
        self.project_id = project_id
        self.project_name = project_name
        self.build_quantity = build_quantity
        self.lines = lines
        super().__init__("Insufficient inventory for the requested project build.")


def consume_project(session: Session, project_id: int, build_quantity: int) -> dict[str, object]:
    if build_quantity <= 0:
        raise BuildValidationError("Build quantity must be greater than zero.")

    if session.in_transaction():
        session.rollback()

    with session.begin():
        project = session.scalar(
            select(Project).where(Project.id == project_id).with_for_update()
        )
        if project is None:
            raise ProjectNotFoundError(f"Project {project_id} was not found.")

        bom_items = session.scalars(
            select(ProjectBomItem)
            .options(joinedload(ProjectBomItem.component))
            .where(ProjectBomItem.project_id == project_id)
            .order_by(ProjectBomItem.component_id)
        ).unique().all()
        if not bom_items:
            raise BuildValidationError(f"Project {project_id} has no BOM items.")

        component_ids = [item.component_id for item in bom_items]
        inventory_items = session.scalars(
            select(InventoryItem)
            .where(InventoryItem.component_id.in_(component_ids))
            .with_for_update()
        ).all()
        inventory_by_component = {item.component_id: item for item in inventory_items}

        lines: list[BuildLine] = []
        for bom_item in bom_items:
            required = bom_item.quantity_required * build_quantity
            inventory = inventory_by_component.get(bom_item.component_id)
            previous_available = inventory.available_quantity if inventory else 0
            shortage = max(required - previous_available, 0)
            lines.append(BuildLine(
                component_id=bom_item.component_id,
                manufacturer_part_number=bom_item.component.manufacturer_part_number,
                required_quantity=required,
                previous_available_quantity=previous_available,
                consumed_quantity=required if shortage == 0 else 0,
                remaining_available_quantity=previous_available - required if shortage == 0 else previous_available,
                shortage_quantity=shortage,
            ))

        shortages = [line for line in lines if line.shortage_quantity > 0]
        if shortages:
            raise BuildShortageError(project_id, project.name, build_quantity, lines)

        build = ProjectBuild(
            project_id=project_id,
            build_quantity=build_quantity,
            status=ProjectBuildStatus.COMPLETED,
        )
        session.add(build)
        session.flush()

        for bom_item, line in zip(bom_items, lines):
            inventory = inventory_by_component[bom_item.component_id]
            inventory.quantity_on_hand -= line.consumed_quantity
            if inventory.quantity_on_hand < 0:
                raise BuildValidationError("Inventory cannot become negative.")
            session.add(InventoryTransaction(
                component_id=bom_item.component_id,
                inventory_item_id=inventory.id,
                transaction_type=InventoryTransactionType.BUILD_CONSUMPTION,
                quantity_delta=-line.consumed_quantity,
                reference_type="project_build",
                reference_id=build.id,
                notes=f"Consumed for project {project.name} build",
            ))
            session.add(ProjectBuildItem(
                build_id=build.id,
                component_id=bom_item.component_id,
                quantity_required=line.required_quantity,
                quantity_consumed=line.consumed_quantity,
                shortage_quantity=0,
            ))

        build_id = build.id

    return {
        "project": {"id": project.id, "name": project.name},
        "build_quantity": build_quantity,
        "success": True,
        "build_id": build_id,
        "required_components": [line.__dict__ for line in lines],
        "shortages": [],
    }
