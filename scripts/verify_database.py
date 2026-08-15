import sqlite3
from pathlib import Path


database_path = Path("data/inventory.db")

connection = sqlite3.connect(database_path)
cursor = connection.cursor()

cursor.execute("PRAGMA foreign_keys = ON;")


print("=" * 60)
print("DATABASE VERIFICATION")
print("=" * 60)


# --------------------------------------------------
# 1. Basic counts
# --------------------------------------------------

print("\nDATABASE COUNTS")
print("-" * 60)

cursor.execute("SELECT COUNT(*) FROM components")
components = cursor.fetchone()[0]

cursor.execute("SELECT COUNT(*) FROM projects")
projects = cursor.fetchone()[0]

cursor.execute("SELECT COUNT(*) FROM bom_items")
bom_items = cursor.fetchone()[0]

print(f"Components: {components}")
print(f"Projects:   {projects}")
print(f"BOM items:  {bom_items}")


# --------------------------------------------------
# 2. List projects
# --------------------------------------------------

print("\nPROJECTS")
print("-" * 60)

cursor.execute("""
    SELECT id, name
    FROM projects
    ORDER BY name
""")

for project_id, name in cursor.fetchall():
    print(f"{project_id}: {name}")


# --------------------------------------------------
# 3. Project statistics
# --------------------------------------------------

print("\nPROJECT STATISTICS")
print("-" * 60)

cursor.execute("""
    SELECT
        p.name,
        COUNT(b.id) AS component_count,
        COALESCE(SUM(b.quantity_required), 0) AS required_units
    FROM projects p
    LEFT JOIN bom_items b
        ON p.id = b.project_id
    GROUP BY p.id, p.name
    ORDER BY p.name
""")

for name, component_count, required_units in cursor.fetchall():
    print(
        f"{name}: "
        f"{component_count} components, "
        f"{required_units} required units"
    )


# --------------------------------------------------
# 4. Shared components
# --------------------------------------------------

print("\nSHARED COMPONENTS")
print("-" * 60)

cursor.execute("""
    SELECT
        c.manufacturer_part_number,
        COUNT(DISTINCT b.project_id) AS project_count
    FROM components c
    JOIN bom_items b
        ON c.id = b.component_id
    GROUP BY c.id, c.manufacturer_part_number
    HAVING COUNT(DISTINCT b.project_id) > 1
    ORDER BY c.manufacturer_part_number
""")

shared_components = cursor.fetchall()

for part_number, project_count in shared_components:

    cursor.execute("""
        SELECT p.name
        FROM projects p
        JOIN bom_items b
            ON p.id = b.project_id
        JOIN components c
            ON c.id = b.component_id
        WHERE c.manufacturer_part_number = ?
        ORDER BY p.name
    """, (part_number,))

    project_names = [row[0] for row in cursor.fetchall()]

    print(
        f"{part_number} "
        f"-> {', '.join(project_names)}"
    )

print(f"\nShared components: {len(shared_components)}")


# --------------------------------------------------
# 5. Sample relationship query
# --------------------------------------------------

print("\nSAMPLE PROJECT: ESP32 LCD V2")
print("-" * 60)

cursor.execute("""
    SELECT
        c.manufacturer_part_number,
        c.manufacturer,
        b.quantity_required,
        b.reference_designators
    FROM projects p
    JOIN bom_items b
        ON p.id = b.project_id
    JOIN components c
        ON c.id = b.component_id
    WHERE p.name = 'ESP32 LCD V2'
    ORDER BY c.manufacturer_part_number
""")

rows = cursor.fetchall()

for part_number, manufacturer, quantity, references in rows:
    print(
        f"{part_number} | "
        f"{manufacturer} | "
        f"Qty: {quantity} | "
        f"Refs: {references}"
    )


# --------------------------------------------------
# 6. Check for orphan records
# --------------------------------------------------

print("\nINTEGRITY CHECK")
print("-" * 60)

cursor.execute("""
    SELECT COUNT(*)
    FROM bom_items b
    LEFT JOIN projects p
        ON b.project_id = p.id
    WHERE p.id IS NULL
""")

orphan_projects = cursor.fetchone()[0]

cursor.execute("""
    SELECT COUNT(*)
    FROM bom_items b
    LEFT JOIN components c
        ON b.component_id = c.id
    WHERE c.id IS NULL
""")

orphan_components = cursor.fetchone()[0]

print(f"Orphan project relationships:   {orphan_projects}")
print(f"Orphan component relationships: {orphan_components}")


# --------------------------------------------------
# Finish
# --------------------------------------------------

connection.close()

print("\n" + "=" * 60)
print("VERIFICATION COMPLETE")
print("=" * 60)