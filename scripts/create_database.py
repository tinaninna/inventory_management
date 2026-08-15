import sqlite3
from pathlib import Path


# Database location
database_path = Path("data/inventory.db")

# Make sure the data directory exists
database_path.parent.mkdir(parents=True, exist_ok=True)


# Connect to SQLite
connection = sqlite3.connect(database_path)

cursor = connection.cursor()


# Enable foreign keys
cursor.execute("PRAGMA foreign_keys = ON;")


# --------------------------------------------------
# Components
# --------------------------------------------------

cursor.execute("""
CREATE TABLE IF NOT EXISTS components (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    manufacturer_part_number TEXT NOT NULL UNIQUE,
    description TEXT,
    value TEXT,
    manufacturer TEXT
);
""")


# --------------------------------------------------
# Projects
# --------------------------------------------------

cursor.execute("""
CREATE TABLE IF NOT EXISTS projects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE
);
""")


# --------------------------------------------------
# BOM Items
# --------------------------------------------------

cursor.execute("""
CREATE TABLE IF NOT EXISTS bom_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    project_id INTEGER NOT NULL,

    component_id INTEGER NOT NULL,

    quantity_required INTEGER NOT NULL,

    reference_designators TEXT,

    FOREIGN KEY (project_id)
        REFERENCES projects(id),

    FOREIGN KEY (component_id)
        REFERENCES components(id),

    UNIQUE(project_id, component_id)
);
""")


connection.commit()
connection.close()


print("=" * 60)
print("DATABASE CREATED")
print("=" * 60)
print(f"Database: {database_path}")
print()
print("Tables:")
print("  - components")
print("  - projects")
print("  - bom_items")