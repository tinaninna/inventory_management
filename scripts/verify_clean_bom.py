from pathlib import Path
import pandas as pd


file_path = Path("data/cleaned/bom_cleaned.xlsx")

df = pd.read_excel(file_path)

print("=" * 60)
print("CLEANED BOM VERIFICATION")
print("=" * 60)

print(f"\nRows: {len(df)}")
print(f"Columns: {len(df.columns)}")

print("\nColumns:")
for column in df.columns:
    print(f"  - {column}")

print("\nMissing values:")
print(df.isna().sum())

print("\nUnique manufacturers:")
print(df["Manufacturer"].unique())

print("\nUnique part numbers:")
print(df["MANUFACTURER_PART_NUMBER"].nunique())

print("\nDuplicate rows:")
print(df.duplicated().sum())

print("\nFirst 10 rows:")
print(df.head(10).to_string(index=False))

print("\n" + "=" * 60)
print("VERIFICATION COMPLETE")
print("=" * 60)