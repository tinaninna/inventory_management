from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class BuildRequest(BaseModel):
    quantity: int = Field(gt=0)


class BuildLineResponse(BaseModel):
    component_id: int
    manufacturer_part_number: str
    required_quantity: int
    previous_available_quantity: int
    consumed_quantity: int
    remaining_available_quantity: int
    shortage_quantity: int


class BuildResponse(BaseModel):
    project: dict[str, int | str]
    build_quantity: int
    success: bool
    build_id: int | None = None
    required_components: list[BuildLineResponse]
    shortages: list[BuildLineResponse]


class BuildHistoryItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: int
    build_quantity: int
    status: str
    notes: str | None
    created_at: datetime
