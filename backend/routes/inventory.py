from __future__ import annotations

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from backend.db import get_db
from backend.inventory_import import InventoryImportError, import_inventory
from backend.models_sqlalchemy import ImportJob, InventoryItem

router = APIRouter(prefix="/api/inventory", tags=["inventory"])


def _inventory_item(item: InventoryItem) -> dict[str, object]:
    available = item.available_quantity
    return {
        "id": item.id,
        "component_id": item.component_id,
        "manufacturer_part_number": item.component.manufacturer_part_number,
        "description": item.component.description,
        "value": item.component.value,
        "manufacturer": item.component.manufacturer,
        "quantity_on_hand": item.quantity_on_hand,
        "quantity_reserved": item.quantity_reserved,
        "available_quantity": available,
        "reorder_point": item.reorder_point,
        "requires_reorder": available <= item.reorder_point,
    }


@router.post("/import", status_code=status.HTTP_200_OK)
def upload_inventory(file: UploadFile = File(...), db: Session = Depends(get_db)):
    if not file.filename:
        raise HTTPException(status_code=400, detail="An Excel file is required.")
    try:
        return import_inventory(db, file.file, file.filename)
    except InventoryImportError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("")
def get_inventory(db: Session = Depends(get_db)):
    items = db.scalars(
        select(InventoryItem).options(joinedload(InventoryItem.component)).order_by(InventoryItem.id)
    ).unique().all()
    return [_inventory_item(item) for item in items]


@router.get("/low-stock")
def get_low_stock(db: Session = Depends(get_db)):
    items = db.scalars(
        select(InventoryItem).options(joinedload(InventoryItem.component)).where(
            InventoryItem.quantity_on_hand - InventoryItem.quantity_reserved <= InventoryItem.reorder_point
        ).order_by(InventoryItem.id)
    ).unique().all()
    return [_inventory_item(item) for item in items]


@router.get("/imports")
def get_imports(db: Session = Depends(get_db)):
    jobs = db.scalars(select(ImportJob).order_by(ImportJob.id.desc())).all()
    return [
        {
            "id": job.id,
            "filename": job.file_name,
            "status": job.status.value if hasattr(job.status, "value") else job.status,
            "started_at": job.started_at,
            "completed_at": job.completed_at,
            "rows_processed": job.rows_processed,
            "new_components": job.new_components,
            "updated_components": job.updated_components,
            "unchanged_components": job.unchanged_components,
            "invalid_rows": job.invalid_rows,
            "unmatched_rows": job.unmatched_rows,
            "summary": job.summary,
        }
        for job in jobs
    ]