from __future__ import annotations

from datetime import datetime
from enum import Enum as PyEnum

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.db import Base


class ImportStatus(PyEnum):
    PENDING = "pending"
    IMPORTING = "importing"
    COMPLETED = "completed"
    FAILED = "failed"


class InventoryTransactionType(PyEnum):
    RECEIPT = "receipt"
    ADJUSTMENT = "adjustment"
    BUILD_CONSUMPTION = "build_consumption"
    RESERVATION = "reservation"
    RELEASE = "release"
    IMPORT = "import"


class ProjectBuildStatus(PyEnum):
    PENDING = "pending"
    COMPLETED = "completed"
    REJECTED = "rejected"


class Component(Base):
    __tablename__ = "components"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    manufacturer_part_number: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    value: Mapped[str | None] = mapped_column(String(255), nullable=True)
    manufacturer: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    inventory_item: Mapped["InventoryItem | None"] = relationship(back_populates="component")
    bom_items: Mapped[list["ProjectBomItem"]] = relationship(back_populates="component")
    transactions: Mapped[list["InventoryTransaction"]] = relationship(back_populates="component")


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    bom_items: Mapped[list["ProjectBomItem"]] = relationship(back_populates="project")
    builds: Mapped[list["ProjectBuild"]] = relationship(back_populates="project")


class ProjectBomItem(Base):
    __tablename__ = "project_bom_items"
    __table_args__ = (UniqueConstraint("project_id", "component_id", name="uq_project_component_bom"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    component_id: Mapped[int] = mapped_column(ForeignKey("components.id", ondelete="CASCADE"), nullable=False, index=True)
    quantity_required: Mapped[int] = mapped_column(Integer, nullable=False)
    reference_designators: Mapped[str | None] = mapped_column(Text, nullable=True)

    project: Mapped[Project] = relationship(back_populates="bom_items")
    component: Mapped[Component] = relationship(back_populates="bom_items")


class InventoryItem(Base):
    __tablename__ = "inventory_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    component_id: Mapped[int] = mapped_column(ForeignKey("components.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    quantity_on_hand: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    quantity_reserved: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    reorder_point: Mapped[int] = mapped_column(Integer, nullable=False, default=6)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    component: Mapped[Component] = relationship(back_populates="inventory_item")
    transactions: Mapped[list["InventoryTransaction"]] = relationship(back_populates="inventory_item")

    @property
    def available_quantity(self) -> int:
        return self.quantity_on_hand - self.quantity_reserved


class InventoryTransaction(Base):
    __tablename__ = "inventory_transactions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    component_id: Mapped[int] = mapped_column(ForeignKey("components.id", ondelete="CASCADE"), nullable=False, index=True)
    inventory_item_id: Mapped[int | None] = mapped_column(ForeignKey("inventory_items.id", ondelete="SET NULL"), nullable=True, index=True)
    transaction_type: Mapped[str] = mapped_column(
        Enum(InventoryTransactionType, native_enum=False, validate_strings=True),
        nullable=False,
        index=True,
    )
    quantity_delta: Mapped[int] = mapped_column(Integer, nullable=False)
    reference_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    reference_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    component: Mapped[Component] = relationship(back_populates="transactions")
    inventory_item: Mapped[InventoryItem | None] = relationship(back_populates="transactions")


class ImportJob(Base):
    __tablename__ = "import_jobs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    source_type: Mapped[str] = mapped_column(String(50), nullable=False, default="inventory_excel")
    status: Mapped[str] = mapped_column(
        Enum(ImportStatus, native_enum=False, validate_strings=True),
        nullable=False,
        default=ImportStatus.PENDING,
        index=True,
    )
    uploaded_by: Mapped[str | None] = mapped_column(String(255), nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    rows_processed: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    new_components: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    updated_components: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    unchanged_components: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    invalid_rows: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    unmatched_rows: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class ProjectBuild(Base):
    __tablename__ = "project_builds"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    build_quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    status: Mapped[str] = mapped_column(
        Enum(ProjectBuildStatus, native_enum=False, validate_strings=True),
        nullable=False,
        default=ProjectBuildStatus.PENDING,
        index=True,
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    project: Mapped[Project] = relationship(back_populates="builds")
    build_items: Mapped[list["ProjectBuildItem"]] = relationship(back_populates="build")


class ProjectBuildItem(Base):
    __tablename__ = "project_build_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    build_id: Mapped[int] = mapped_column(ForeignKey("project_builds.id", ondelete="CASCADE"), nullable=False, index=True)
    component_id: Mapped[int] = mapped_column(ForeignKey("components.id", ondelete="CASCADE"), nullable=False, index=True)
    quantity_required: Mapped[int] = mapped_column(Integer, nullable=False)
    quantity_consumed: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    shortage_quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    build: Mapped[ProjectBuild] = relationship(back_populates="build_items")
    component: Mapped[Component] = relationship()
