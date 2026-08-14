from pathlib import Path
import pandas as pd


# --------------------------------------------------
# File paths
# --------------------------------------------------

input_file = Path("data/raw/merged all to be ordered.xlsx")
output_file = Path("data/cleaned/bom_cleaned.xlsx")


# --------------------------------------------------
# Load raw data
# --------------------------------------------------

df = pd.read_excel(
    input_file,
    sheet_name="Bill of Materials"
)

print(f"Loaded {len(df)} rows")


# --------------------------------------------------
# Remove completely empty columns
# --------------------------------------------------

empty_columns = [
    column
    for column in df.columns
    if df[column].isna().all()
]

print("\nCompletely empty columns:")
for column in empty_columns:
    print(f"  - {column}")

df = df.drop(columns=empty_columns)


# --------------------------------------------------
# Clean text columns
# --------------------------------------------------

text_columns = df.select_dtypes(
    include=["object", "string"]
).columns

for column in text_columns:
    df[column] = df[column].apply(
        lambda value: value.strip()
        if isinstance(value, str)
        else value
    )


# --------------------------------------------------
# Normalize missing text values
# --------------------------------------------------

df[text_columns] = df[text_columns].fillna("")


# --------------------------------------------------
# Normalize manufacturer names
# --------------------------------------------------

manufacturer_mapping = {
    "Kemet": "KEMET",
    "KEMET": "KEMET",

    "YAGEO": "Yageo",
    "Yageo": "Yageo",

    "TAIYO YUDEN": "Taiyo Yuden",
    "Taiyo Yuden": "Taiyo Yuden",

    "LITTELFUSE": "Littelfuse",
    "Littelfuse Inc": "Littelfuse",
    "Littelfuse Inc.": "Littelfuse",
}

df["Manufacturer"] = (
    df["Manufacturer"]
    .replace(manufacturer_mapping)
)


# --------------------------------------------------
# Validate required fields
# --------------------------------------------------

required_columns = [
    "MANUFACTURER_PART_NUMBER",
    "Quantity",
    "Reference Designators",
    "Customer Reference",
]

print("\nRequired field validation:")

for column in required_columns:
    missing = df[column].isna().sum()

    if missing == 0:
        print(f"  ✓ {column}")
    else:
        print(f"  ✗ {column}: {missing} missing")


# --------------------------------------------------
# Save cleaned dataset
# --------------------------------------------------

df.to_excel(
    output_file,
    index=False
)

print("\n" + "=" * 60)
print("CLEANING COMPLETE")
print("=" * 60)

print(f"Rows: {len(df)}")
print(f"Columns: {len(df.columns)}")
print(f"Output: {output_file}")