from __future__ import annotations

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from backend.db import Base
from backend.models_sqlalchemy import (
    Component,
    InventoryItem,
    InventoryTransaction,
    InventoryTransactionType,
    Project,
    ProjectBomItem,
    ProjectBuild,
    ProjectBuildItem,
)
from backend.project_consumption import (
    BuildShortageError,
    BuildValidationError,
    consume_project,
)


@pytest.fixture
def session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine)
    with factory() as database:
        yield database


def add_project(session, quantities, stock=None):
    project = Project(id=1, name="Build project")
    session.add(project)
    for index, quantity in enumerate(quantities, start=1):
        component = Component(id=index, manufacturer_part_number=f"PART-{index}")
        session.add(component)
        session.add(ProjectBomItem(project=project, component=component, quantity_required=quantity))
        if stock is not None and index in stock:
            session.add(InventoryItem(component=component, quantity_on_hand=stock[index], quantity_reserved=0, reorder_point=6))
    session.commit()
    return project


def test_sufficient_build_consumes_inventory_and_creates_records(session):
    add_project(session, [2, 3], {1: 10, 2: 10})

    result = consume_project(session, 1, 2)

    assert result["success"] is True
    assert result["build_id"] == 1
    assert [line["required_quantity"] for line in result["required_components"]] == [4, 6]
    assert session.get(InventoryItem, 1).quantity_on_hand == 6
    assert session.get(InventoryItem, 2).quantity_on_hand == 4
    assert session.scalar(select(ProjectBuild)) is not None
    assert session.scalar(select(ProjectBuildItem)) is not None
    transactions = session.scalars(select(InventoryTransaction)).all()
    assert len(transactions) == 2
    assert all(transaction.transaction_type == InventoryTransactionType.BUILD_CONSUMPTION for transaction in transactions)
    assert all(transaction.quantity_delta < 0 for transaction in transactions)


def test_required_quantity_is_bom_quantity_times_build_quantity(session):
    add_project(session, [4], {1: 20})

    result = consume_project(session, 1, 3)

    assert result["required_components"][0]["required_quantity"] == 12
    assert result["required_components"][0]["consumed_quantity"] == 12
    assert session.get(InventoryItem, 1).quantity_on_hand == 8


def test_one_shortage_rejects_entire_build_without_changes(session):
    add_project(session, [4, 2], {1: 4, 2: 20})
    before = [session.get(InventoryItem, index).quantity_on_hand for index in (1, 2)]

    with pytest.raises(BuildShortageError) as error:
        consume_project(session, 1, 2)

    assert len(error.value.lines) == 2
    assert [line.shortage_quantity for line in error.value.lines] == [4, 0]
    assert [session.get(InventoryItem, index).quantity_on_hand for index in (1, 2)] == before
    assert session.scalar(select(ProjectBuild)) is None
    assert session.scalar(select(InventoryTransaction)) is None


def test_multiple_shortages_are_all_returned(session):
    add_project(session, [5, 7, 2], {1: 1, 2: 2})

    with pytest.raises(BuildShortageError) as error:
        consume_project(session, 1, 1)

    assert [(line.component_id, line.shortage_quantity) for line in error.value.lines if line.shortage_quantity] == [(1, 4), (2, 5), (3, 2)]


def test_missing_inventory_is_zero_and_causes_shortage(session):
    add_project(session, [1], {})

    with pytest.raises(BuildShortageError) as error:
        consume_project(session, 1, 1)

    assert error.value.lines[0].previous_available_quantity == 0
    assert error.value.lines[0].shortage_quantity == 1
    assert session.scalar(select(InventoryTransaction)) is None


@pytest.mark.parametrize("quantity", [0, -1])
def test_non_positive_build_quantity_is_rejected(session, quantity):
    add_project(session, [1], {1: 10})

    with pytest.raises(BuildValidationError):
        consume_project(session, 1, quantity)


def test_inventory_never_becomes_negative(session):
    add_project(session, [3], {1: 2})

    with pytest.raises(BuildShortageError):
        consume_project(session, 1, 1)

    assert session.get(InventoryItem, 1).quantity_on_hand == 2
    assert session.get(InventoryItem, 1).quantity_on_hand >= 0
