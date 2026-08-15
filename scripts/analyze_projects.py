from pathlib import Path
import pandas as pd


# --------------------------------------------------
# Load cleaned BOM
# --------------------------------------------------

file_path = Path("data/cleaned/bom_cleaned.xlsx")

df = pd.read_excel(file_path)

print("=" * 70)
print("PROJECT / COMPONENT ANALYSIS")
print("=" * 70)


# --------------------------------------------------
# Extract project names
# --------------------------------------------------

def extract_projects(customer_reference):
    """
    Extract project names from the Customer Reference field.

    The ESP32 project contains a comma inside its date:
    ESP32 LCD V2 (July 28,2026)

    Therefore we cannot simply split the entire field by commas.
    """

    value = str(customer_reference).strip()

    projects = []

    # Extract ESP32 LCD V2 if present
    if "ESP32 LCD V2" in value:
        projects.append("ESP32 LCD V2")

    # Extract Renesas_BMS if present
    if "Renesas_BMS" in value:
        projects.append("Renesas_BMS")

    # Extract TOP_COOLED_V3 if present
    if "TOP_COOLED_V3" in value:
        projects.append("TOP_COOLED_V3")

    return projects


df["Projects"] = df["Customer Reference"].apply(extract_projects)


# --------------------------------------------------
# Display discovered projects
# --------------------------------------------------

all_projects = sorted(
    {
        project
        for projects in df["Projects"]
        for project in projects
    }
)

print("\nProjects discovered:")

for project in all_projects:
    print(f"  - {project}")

print(f"\nTotal projects: {len(all_projects)}")


# --------------------------------------------------
# Project statistics
# --------------------------------------------------

print("\n" + "=" * 70)
print("PROJECT STATISTICS")
print("=" * 70)

for project in all_projects:

    project_rows = df[
        df["Projects"].apply(
            lambda projects: project in projects
        )
    ]

    component_count = len(project_rows)

    total_quantity = project_rows["Quantity"].sum()

    print(f"\nProject: {project}")
    print(f"  Components: {component_count}")
    print(f"  Required units: {total_quantity}")


# --------------------------------------------------
# Shared components
# --------------------------------------------------

print("\n" + "=" * 70)
print("SHARED COMPONENTS")
print("=" * 70)

for _, row in df.iterrows():

    projects = row["Projects"]

    if len(projects) > 1:

        print(
            f"\n{row['MANUFACTURER_PART_NUMBER']}"
        )

        print(
            f"  Quantity: {row['Quantity']}"
        )

        print(
            f"  Projects: {', '.join(projects)}"
        )


# --------------------------------------------------
# Project-component relationship table
# --------------------------------------------------

relationships = []

for _, row in df.iterrows():

    for project in row["Projects"]:

        relationships.append({
            "Project": project,
            "MANUFACTURER_PART_NUMBER":
                row["MANUFACTURER_PART_NUMBER"],
            "Quantity": row["Quantity"],
            "Reference Designators":
                row["Reference Designators"],
        })


relationship_df = pd.DataFrame(relationships)


print("\n" + "=" * 70)
print("RELATIONSHIP TABLE")
print("=" * 70)

print(
    relationship_df.to_string(index=False)
)


# --------------------------------------------------
# Save relationship data
# --------------------------------------------------

output_file = Path(
    "data/cleaned/project_bom_relationships.xlsx"
)

relationship_df.to_excel(
    output_file,
    index=False
)

print("\n" + "=" * 70)
print("ANALYSIS COMPLETE")
print("=" * 70)

print(f"Relationship rows: {len(relationship_df)}")
print(f"Output: {output_file}")