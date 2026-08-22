from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path
from typing import BinaryIO

import pandas as pd
from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from backend.models_sqlalchemy import (
    Component,
    ImportJob,
    ImportStatus,
    InventoryItem,
    InventoryTransaction,
    InventoryTransactionType,
)

REORDER_POINT = 6
SUPPORTED_EXTENSIONS = {".xlsx", ".xls"}
_COLUMN_ALIASES = {
    "manufacturer_part_number": {
        "manufacturerpartnumber", "mpn", "partnumber", "partno", "part",
    },
    "quantity": {"quantity", "qty", "quantityonhand", "onhand", "stock", "inventory"},
    "description": {"description", "desc", "componentdescription"},
    "value": {"value", "componentvalue"},
    "manufacturer": {"manufacturer", "maker", "vendor"},
}


class InventoryImportError(ValueError):
    pass


@dataclass(frozen=True)
class ImportRow:
    part_number: str
    quantity: int
    description: str | None = None
    value: str | None = None
    manufacturer: str | None = None


def _normalized_column(value: object) -> str:
    return re.sub(r"[^a-z0-9]", "", str(value).strip().lower())


def normalize_part_number(value: object) -> str:
    if value is None or pd.isna(value):
        return ""
    return re.sub(r"\s+", "", str(value).strip()).upper()


# Separators that suggest a cell accidentally contains more than one part number
# (e.g. "T1,T2" from a copy/paste mistake). Rows with these are rejected outright
# rather than imported as a single bogus component.
_MULTI_VALUE_PATTERN = re.compile(r"[,;]")


def loose_part_number_key(value: object) -> str:
    """Strip all punctuation/whitespace so formatting-only differences
    (ABC-123 vs ABC 123 vs abc123) collapse to the same key. Never used for
    storage or display — matching only. It will never merge two part numbers
    that differ by any actual character (e.g. R100 vs R1000 stay distinct)."""
    return re.sub(r"[^A-Z0-9]", "", normalize_part_number(value))


def normalize_text(value: object) -> str | None:
    if value is None or pd.isna(value):
        return None
    text = str(value).strip()
    return text or None


def identify_columns(columns: list[object]) -> dict[str, object]:
    normalized = {_normalized_column(column): column for column in columns}
    identified: dict[str, object] = {}
    for field, aliases in _COLUMN_ALIASES.items():
        matches = [normalized[alias] for alias in aliases if alias in normalized]
        if matches:
            identified[field] = matches[0]
    required = {"manufacturer_part_number", "quantity"}
    missing = sorted(required - identified.keys())
    if missing:
        raise InventoryImportError(
            "Required inventory columns could not be identified: " + ", ".join(missing)
        )
    return identified


def parse_inventory_workbook(file: BinaryIO, filename: str) -> tuple[list[ImportRow], int, int, list[str]]:
    extension = Path(filename or "").suffix.lower()
    if extension not in SUPPORTED_EXTENSIONS:
        raise InventoryImportError("Unsupported file type. Upload an .xlsx or .xls workbook.")
    try:
        workbook = pd.ExcelFile(file)
        sheet = "Bill of Materials" if "Bill of Materials" in workbook.sheet_names else workbook.sheet_names[0]
        frame = pd.read_excel(workbook, sheet_name=sheet)
    except Exception as exc:
        raise InventoryImportError(f"The workbook could not be opened: {exc}") from exc
    if frame.empty:
        raise InventoryImportError("The workbook contains no data rows.")

    columns = identify_columns(list(frame.columns))
    rows: list[ImportRow] = []
    invalid: list[str] = []
    seen: dict[str, int] = {}
    for index, record in frame.iterrows():
        part_number = normalize_part_number(record[columns["manufacturer_part_number"]])
        raw_quantity = record[columns["quantity"]]
        try:
            quantity = int(float(raw_quantity))
            if quantity < 0:
                raise ValueError
        except (TypeError, ValueError, OverflowError):
            invalid.append(f"row {index + 2}: quantity must be a non-negative integer")
            continue
        if not part_number:
            invalid.append(f"row {index + 2}: manufacturer part number is required")
            continue
        if _MULTI_VALUE_PATTERN.search(part_number):
            invalid.append(f"row {index + 2}: part number '{part_number}' appears to contain multiple values")
            continue
        if part_number in seen and seen[part_number] != quantity:
            invalid.append(f"row {index + 2}: conflicting duplicate for {part_number}")
            continue
        if part_number in seen:
            continue
        seen[part_number] = quantity
        rows.append(ImportRow(
            part_number=part_number,
            quantity=quantity,
            description=normalize_text(record[columns["description"]]) if "description" in columns else None,
            value=normalize_text(record[columns["value"]]) if "value" in columns else None,
            manufacturer=normalize_text(record[columns["manufacturer"]]) if "manufacturer" in columns else None,
        ))
    return rows, len(frame), len(invalid), invalid


def import_inventory(session: Session, file: BinaryIO, filename: str) -> dict[str, object]:
    started_at = datetime.now(timezone.utc)
    rows, source_row_count, invalid_count, invalid_details = parse_inventory_workbook(file, filename)
    job = ImportJob(file_name=filename, status=ImportStatus.IMPORTING, started_at=started_at)
    session.add(job)
    session.flush()
    counts = {"new_components": 0, "updated_components": 0, "unchanged_components": 0}
    flagged_matches: list[str] = []
    try:
        part_numbers = {row.part_number for row in rows}
        loose_keys = {loose_part_number_key(row.part_number) for row in rows}
        existing = session.scalars(
            select(Component).options(joinedload(Component.inventory_item)).where(
                Component.manufacturer_part_number.in_(part_numbers) | Component.part_number_key.in_(loose_keys)
            )
        ).unique().all() if part_numbers else []
        by_part_number = {component.manufacturer_part_number: component for component in existing}
        by_loose_key: dict[str, Component] = {}
        for component in existing:
            by_loose_key.setdefault(component.part_number_key, component)

        for row in rows:
            component = by_part_number.get(row.part_number)
            matched_by_loose_key = False
            if component is None:
                loose_key = loose_part_number_key(row.part_number)
                component = by_loose_key.get(loose_key)
                matched_by_loose_key = component is not None
            if matched_by_loose_key:
                flagged_matches.append(
                    f"'{row.part_number}' matched existing component '{component.manufacturer_part_number}' "
                    "by normalized formatting only — verify these are the same part"
                )
            if component is None:
                component = Component(
                    manufacturer_part_number=row.part_number,
                    part_number_key=loose_part_number_key(row.part_number),
                    description=row.description,
                    value=row.value,
                    manufacturer=row.manufacturer,
                )
                session.add(component)
                session.flush()
                inventory = InventoryItem(component=component, quantity_on_hand=row.quantity, reorder_point=REORDER_POINT)
                session.add(inventory)
                session.flush()
                session.add(InventoryTransaction(
                    component=component,
                    inventory_item=inventory,
                    transaction_type=InventoryTransactionType.IMPORT,
                    quantity_delta=row.quantity,
                    reference_type="import_job",
                    reference_id=job.id,
                    notes="Initial inventory import",
                ))
                counts["new_components"] += 1
                by_part_number[component.manufacturer_part_number] = component
                by_loose_key.setdefault(component.part_number_key, component)
                continue

            if row.description and not component.description:
                component.description = row.description
            if row.value and not component.value:
                component.value = row.value
            if row.manufacturer and not component.manufacturer:
                component.manufacturer = row.manufacturer
            inventory = component.inventory_item
            if inventory is None:
                inventory = InventoryItem(component=component, quantity_on_hand=0, reorder_point=REORDER_POINT)
                session.add(inventory)
                session.flush()
            inventory.reorder_point = REORDER_POINT
            delta = row.quantity - inventory.quantity_on_hand
            if delta == 0:
                counts["unchanged_components"] += 1
                continue
            inventory.quantity_on_hand = row.quantity
            session.add(InventoryTransaction(
                component=component,
                inventory_item=inventory,
                transaction_type=InventoryTransactionType.IMPORT,
                quantity_delta=delta,
                reference_type="import_job",
                reference_id=job.id,
                notes="Inventory quantity updated by import",
            ))
            counts["updated_components"] += 1

        job.status = ImportStatus.COMPLETED
        job.completed_at = datetime.now(timezone.utc)
        job.rows_processed = source_row_count
        job.new_components = counts["new_components"]
        job.updated_components = counts["updated_components"]
        job.unchanged_components = counts["unchanged_components"]
        job.invalid_rows = invalid_count
        job.unmatched_rows = 0
        job.summary = json.dumps({"invalid_details": invalid_details, "flagged_matches": flagged_matches})
        session.commit()
    except Exception:
        session.rollback()
        raise

    low_stock = session.scalar(
        select(func.count()).select_from(InventoryItem).where(
            InventoryItem.quantity_on_hand - InventoryItem.quantity_reserved <= REORDER_POINT
        )
    ) or 0
    return {
        "status": "completed",
        "import_job_id": job.id,
        "filename": filename,
        "rows_processed": source_row_count,
        **counts,
        "invalid_rows": invalid_count,
        "unmatched_rows": 0,
        "invalid_details": invalid_details,
        "flagged_matches": flagged_matches,
        "low_stock_components": low_stock,
    }