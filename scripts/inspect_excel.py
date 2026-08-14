from pathlib import Path
import pandas as pd

# Location of the raw Excel file
file_path = Path("data/raw/merged all to be ordered.xlsx")

# Load workbook information
excel_file = pd.ExcelFile(file_path)

print("=" * 60)
print("INVENTORY DATA INSPECTION")
print("=" * 60)

print("\nSheets:")
for sheet in excel_file.sheet_names:
    print(f"  - {sheet}")

# Read the BOM sheet
df = pd.read_excel(file_path, sheet_name="Bill of Materials")

print("\n" + "=" * 60)
print("BASIC INFORMATION")
print("=" * 60)

print(f"Rows: {df.shape[0]}")
print(f"Columns: {df.shape[1]}")

print("\nColumns:")
for column in df.columns:
    print(f"  - {column}")

print("\n" + "=" * 60)
print("DATA TYPES")
print("=" * 60)

print(df.dtypes)

print("\n" + "=" * 60)
print("MISSING VALUES")
print("=" * 60)

missing = df.isna().sum()

for column, count in missing.items():
    print(f"{column}: {count}")

print("\n" + "=" * 60)
print("DUPLICATE ROWS")
print("=" * 60)

print(f"Duplicate rows: {df.duplicated().sum()}")

print("\n" + "=" * 60)
print("FIRST 10 ROWS")
print("=" * 60)

print(df.head(10).to_string(index=False))