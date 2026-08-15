# Inventory Management System - Data Model

## 1. Components

Represents a unique physical/electronic component.

Fields:

- component_id
- manufacturer_part_number
- description
- value
- manufacturer

Source:
Cleaned BOM.

---

## 2. Projects

Represents a product/project that consumes components.

Known projects:

- ESP32 LCD V2
- Renesas_BMS
- TOP_COOLED_V3

Fields:

- project_id
- project_name

---

## 3. BOM Items

Represents the relationship between a project and a component.

Fields:

- bom_item_id
- project_id
- component_id
- quantity_required
- reference_designators

Relationship:

Project -> many BOM Items
Component -> many BOM Items

---

## 4. Inventory

Represents the current stock position of a component.

Potential fields:

- inventory_id
- component_id
- quantity_on_hand
- quantity_reserved
- quantity_on_order
- reorder_level
- reorder_quantity

---

## 5. Suppliers

Potential future entity.

Possible fields:

- supplier_id
- supplier_name
- contact_information

---

## 6. Purchase Orders

Potential future entity.

Possible fields:

- purchase_order_id
- supplier_id
- order_date
- expected_delivery_date
- status

---

## 7. Inventory Transactions

Potential future entity for traceability.

Examples:

- receiving stock
- issuing stock
- adjustment
- reservation
- return

Possible fields:

- transaction_id
- component_id
- transaction_type
- quantity
- timestamp
- reference
- notes