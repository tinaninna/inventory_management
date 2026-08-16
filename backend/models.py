from pydantic import BaseModel


class Component(BaseModel):
    id: int
    manufacturer_part_number: str
    description: str | None
    value: str | None
    manufacturer: str | None


class Project(BaseModel):
    id: int
    name: str


class BOMItem(BaseModel):
    id: int
    component_id: int
    manufacturer_part_number: str
    description: str | None
    value: str | None
    manufacturer: str | None
    quantity_required: int
    reference_designators: str | None