from io import BytesIO
import sqlite3

import pandas as pd
import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from backend.db import Base
from backend.inventory_import import InventoryImportError, import_inventory, parse_inventory_workbook
from backend.migration_seed import MigrationSeedError, migrate_existing_sqlite_data
from backend.models_sqlalchemy import Component, InventoryItem, InventoryTransaction, Project, ProjectBomItem
from backend.routes.bom import get_project_bom
from backend.routes.dashboard import get_dashboard
from backend.routes.projects import get_projects


@pytest.fixture
def session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine)
    with factory() as database:
        yield database


def workbook(rows, columns=None):
    frame = pd.DataFrame(rows, columns=columns)
    output = BytesIO()
    frame.to_excel(output, index=False, engine="openpyxl")
    output.seek(0)
    return output


def test_valid_excel_parsing_and_column_aliases():
    rows, total, invalid, details = parse_inventory_workbook(
        workbook([{"MPN": " abc-1 ", "Qty": 4}]), "stock.xlsx"
    )
    assert total == 1
    assert invalid == 0
    assert details == []
    assert rows[0].part_number == "ABC-1"
    assert rows[0].quantity == 4


def test_invalid_file_and_missing_columns():
    with pytest.raises(InventoryImportError, match="Unsupported file type"):
        parse_inventory_workbook(BytesIO(b"not excel"), "stock.csv")
    with pytest.raises(InventoryImportError, match="Required inventory columns"):
        parse_inventory_workbook(workbook([{"Description": "missing"}]), "stock.xlsx")


def test_new_changed_unchanged_and_reorder_summary(session):
    session.add(Component(manufacturer_part_number="OLD-1"))
    session.flush()
    session.add(InventoryItem(component_id=1, quantity_on_hand=5, quantity_reserved=1, reorder_point=6))
    session.commit()

    result = import_inventory(
        session,
        workbook([
            {"Manufacturer Part Number": "OLD-1", "Quantity": 8},
            {"Manufacturer Part Number": "NEW-1", "Quantity": 2},
        ]),
        "inventory.xlsx",
    )

    assert result["new_components"] == 1
    assert result["updated_components"] == 1
    assert result["unchanged_components"] == 0
    assert result["low_stock_components"] == 1
    assert session.scalar(select(InventoryItem).where(InventoryItem.component_id == 1)).quantity_on_hand == 8
    assert session.scalar(select(InventoryTransaction).where(InventoryTransaction.quantity_delta == 3)) is not None

    unchanged = import_inventory(
        session, workbook([{"MPN": "OLD-1", "Quantity": 8}]), "inventory.xlsx"
    )
    assert unchanged["updated_components"] == 0
    assert unchanged["unchanged_components"] == 1


def test_conflicting_duplicates_are_invalid(session):
    result = import_inventory(
        session,
        workbook([
            {"MPN": "DUP-1", "Quantity": 3},
            {"MPN": "dup-1", "Quantity": 4},
        ]),
        "inventory.xlsx",
    )
    assert result["invalid_rows"] == 1
    assert result["new_components"] == 1


def test_failed_database_transaction_rolls_back(session, monkeypatch):
    original_commit = session.commit

    def fail_commit():
        raise RuntimeError("simulated database failure")

    monkeypatch.setattr(session, "commit", fail_commit)
    with pytest.raises(RuntimeError, match="simulated database failure"):
        import_inventory(session, workbook([{"MPN": "ROLLBACK-1", "Quantity": 4}]), "inventory.xlsx")
    session.rollback()
    assert session.scalar(select(Component).where(Component.manufacturer_part_number == "ROLLBACK-1")) is None
    monkeypatch.setattr(session, "commit", original_commit)


def source_database(path, include_unmatched=False):
    with sqlite3.connect(path) as database:
        database.executescript("""
            CREATE TABLE components (id INTEGER PRIMARY KEY, manufacturer_part_number TEXT NOT NULL UNIQUE, description TEXT, value TEXT, manufacturer TEXT);
            CREATE TABLE projects (id INTEGER PRIMARY KEY, name TEXT NOT NULL UNIQUE);
            CREATE TABLE bom_items (id INTEGER PRIMARY KEY, project_id INTEGER NOT NULL, component_id INTEGER NOT NULL, quantity_required INTEGER NOT NULL, reference_designators TEXT);
        """)
        database.execute("INSERT INTO components VALUES (1, 'MATCH-1', 'Matched', NULL, 'Maker')")
        if include_unmatched:
            database.execute("INSERT INTO components VALUES (2, 'MISSING-1', 'Missing', NULL, 'Maker')")
        database.execute("INSERT INTO projects VALUES (1, 'Project A')")
        database.execute("INSERT INTO bom_items VALUES (1, 1, 1, 3, 'R1')")
        if include_unmatched:
            database.execute("INSERT INTO bom_items VALUES (2, 1, 2, 4, 'R2')")
        database.commit()


def test_sqlite_seed_preserves_ids_and_resolves_bom_by_part_number(session, tmp_path):
    source = tmp_path / "inventory.db"
    source_database(source)
    session.add(Component(id=10, manufacturer_part_number="MATCH-1"))
    session.commit()

    result = migrate_existing_sqlite_data(session, source)

    assert result["projects"] == 1
    assert result["bom_items"] == 1
    assert result["unmatched_bom_items"] == []
    assert session.get(Project, 1).name == "Project A"
    item = session.scalar(select(ProjectBomItem))
    assert item.component_id == 10
    assert item.quantity_required == 3


def test_sqlite_seed_strict_mode_rolls_back_unmatched_bom(session, tmp_path):
    source = tmp_path / "inventory.db"
    source_database(source, include_unmatched=True)
    session.add(Component(id=10, manufacturer_part_number="MATCH-1"))
    session.add(Component(id=11, manufacturer_part_number=" MATCH-1"))
    session.commit()

    with pytest.raises(MigrationSeedError) as error:
        migrate_existing_sqlite_data(session, source)

    assert len(error.value.unmatched_bom_items) == 1
    session.rollback()
    assert session.get(Project, 1) is None


def test_project_bom_and_dashboard_routes_read_sqlalchemy(session):
    component = Component(id=10, manufacturer_part_number="MATCH-1", description="Matched")
    project = Project(id=1, name="Project A")
    item = ProjectBomItem(
        id=1, project=project, component=component, quantity_required=3, reference_designators="R1"
    )
    session.add_all([component, project, item])
    session.commit()

    projects = get_projects(session)
    bom = get_project_bom(1, session)
    dashboard = get_dashboard(session)

    assert projects[0]["id"] == 1
    assert bom[0]["component_id"] == 10
    assert dashboard["project_count"] == 1
    assert dashboard["bom_item_count"] == 1
    assert dashboard["projects"][0]["total_quantity_required"] == 3