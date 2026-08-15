import sqlite3
from pathlib import Path

import pandas as pd


# --------------------------------------------------
# File paths
# --------------------------------------------------

database_path = Path("data/inventory.db")

bom_file = Path("data/cleaned/bom_cleaned.xlsx")
relationship_file = Path(
    "data/cleaned/project_bom_relationships.xlsx"
)


# --------------------------------------------------
# Load Excel files
# --------------------------------------------------

print("=" * 60)
print("IMPORTING DATA")
print("=" * 60)

bom_df = pd.read_excel(bom_file)
relationship_df = pd.read_excel(relationship_file)

print(f"\nBOM rows loaded: {len(bom_df)}")
print(f"Relationship rows loaded: {len(relationship_df)}")


# --------------------------------------------------
# Connect to database
# --------------------------------------------------

connection = sqlite3.connect(database_path)

cursor = connection.cursor()

cursor.execute("PRAGMA foreign_keys = ON;")


# --------------------------------------------------
# Import components
# --------------------------------------------------

print("\nImporting components...")

for _, row in bom_df.iterrows():

    cursor.execute(
        """
        INSERT OR IGNORE INTO components (
            manufacturer_part_number,
            description,
            value,
            manufacturer
        )
        VALUES (?, ?, ?, ?)
        """,
        (
            row["MANUFACTURER_PART_NUMBER"],
            row["Description"],
            row["Value"],
            row["Manufacturer"],
        ),
    )


# --------------------------------------------------
# Import projects
# --------------------------------------------------

print("Importing projects...")

projects = relationship_df["Project"].dropna().unique()

for project in projects:

    cursor.execute(
        """
        INSERT OR IGNORE INTO projects (name)
        VALUES (?)
        """,
        (project,),
    )


# --------------------------------------------------
# Import BOM relationships
# --------------------------------------------------

print("Importing BOM relationships...")

for _, row in relationship_df.iterrows():

    project = row["Project"]
    part_number = row["MANUFACTURER_PART_NUMBER"]

    # Get project ID
    cursor.execute(
        """
        SELECT id
        FROM projects
        WHERE name = ?
        """,
        (project,),
    )

    project_result = cursor.fetchone()

    if project_result is None:
        raise ValueError(
            f"Project not found: {project}"
        )

    project_id = project_result[0]

    # Get component ID
    cursor.execute(
        """
        SELECT id
        FROM components
        WHERE manufacturer_part_number = ?
        """,
        (part_number,),
    )

    component_result = cursor.fetchone()

    if component_result is None:
        raise ValueError(
            f"Component not found: {part_number}"
        )

    component_id = component_result[0]

    # Insert relationship
    cursor.execute(
        """
        INSERT OR IGNORE INTO bom_items (
            project_id,
            component_id,
            quantity_required,
            reference_designators
        )
        VALUES (?, ?, ?, ?)
        """,
        (
            project_id,
            component_id,
            int(row["Quantity"]),
            row["Reference Designators"],
        ),
    )


# --------------------------------------------------
# Save changes
# --------------------------------------------------

connection.commit()


# --------------------------------------------------
# Verify counts
# --------------------------------------------------

print("\n" + "=" * 60)
print("DATABASE COUNTS")
print("=" * 60)

cursor.execute("SELECT COUNT(*) FROM components")
component_count = cursor.fetchone()[0]

cursor.execute("SELECT COUNT(*) FROM projects")
project_count = cursor.fetchone()[0]

cursor.execute("SELECT COUNT(*) FROM bom_items")
bom_count = cursor.fetchone()[0]

print(f"Components: {component_count}")
print(f"Projects:   {project_count}")
print(f"BOM items:  {bom_count}")


# --------------------------------------------------
# Close database
# --------------------------------------------------

connection.close()


print("\n" + "=" * 60)
print("IMPORT COMPLETE")
print("=" * 60)