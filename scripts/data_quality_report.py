from pathlib import Path
import pandas as pd

file_path = Path("data/raw/merged all to be ordered.xlsx")

df = pd.read_excel(
    file_path,
    sheet_name="Bill of Materials"
)

print("=" * 70)
print("DATA QUALITY REPORT")
print("=" * 70)

# --------------------------------------------------
# 1. Manufacturer values
# --------------------------------------------------

print("\n" + "=" * 70)
print("MANUFACTURERS")
print("=" * 70)

manufacturers = (
    df["Manufacturer"]
    .dropna()
    .astype(str)
    .str.strip()
    .sort_values()
    .unique()
)

for manufacturer in manufacturers:
    print(manufacturer)

print(f"\nUnique manufacturers: {len(manufacturers)}")


# --------------------------------------------------
# 2. Customer references
# --------------------------------------------------

print("\n" + "=" * 70)
print("CUSTOMER REFERENCES")
print("=" * 70)

references = (
    df["Customer Reference"]
    .dropna()
    .astype(str)
    .str.strip()
    .unique()
)

for reference in references:
    print(reference)

print(f"\nUnique customer references: {len(references)}")


# --------------------------------------------------
# 3. Part numbers
# --------------------------------------------------

print("\n" + "=" * 70)
print("PART NUMBER CHECK")
print("=" * 70)

part_numbers = df["MANUFACTURER_PART_NUMBER"].astype(str).str.strip()

print(f"Total rows: {len(part_numbers)}")
print(f"Unique part numbers: {part_numbers.nunique()}")
print(f"Duplicate part numbers: {part_numbers.duplicated().sum()}")


# --------------------------------------------------
# 4. Quantity statistics
# --------------------------------------------------

print("\n" + "=" * 70)
print("QUANTITY")
print("=" * 70)

print(df["Quantity"].describe())


# --------------------------------------------------
# 5. Missing data percentage
# --------------------------------------------------

print("\n" + "=" * 70)
print("MISSING DATA (%)")
print("=" * 70)

missing_percentage = (
    df.isna()
    .mean()
    .mul(100)
    .sort_values(ascending=False)
)

for column, percentage in missing_percentage.items():
    print(f"{column}: {percentage:.1f}%")


# --------------------------------------------------
# 6. Whitespace checks
# --------------------------------------------------

print("\n" + "=" * 70)
print("WHITESPACE CHECK")
print("=" * 70)

text_columns = df.select_dtypes(include=["object", "string"]).columns

for column in text_columns:
    original = df[column].dropna().astype(str)
    stripped = original.str.strip()

    count = (original != stripped).sum()

    print(f"{column}: {count} values contain leading/trailing spaces")


print("\n" + "=" * 70)
print("REPORT COMPLETE")
print("=" * 70)