import pandas as pd
from pathlib import Path


DATA_PATH = Path("data/raw/yellow_tripdata_2025-01.parquet")


print("=" * 60)
print("RIDEOPS AI - DATASET INSPECTION")
print("=" * 60)

print(f"\nLooking for:")
print(DATA_PATH.resolve())

print(f"\nFile exists: {DATA_PATH.exists()}")

if not DATA_PATH.exists():
    print("\nERROR: Parquet file was not found.")
    raise SystemExit(1)

print("\nReading Parquet file...")
df = pd.read_parquet(DATA_PATH)

print("\nSuccessfully loaded dataset!")

print("\n" + "=" * 60)
print("DATASET SHAPE")
print("=" * 60)

print(f"Rows: {len(df):,}")
print(f"Columns: {len(df.columns)}")


print("\n" + "=" * 60)
print("COLUMNS")
print("=" * 60)

for i, column in enumerate(df.columns, start=1):
    print(f"{i}. {column}")


print("\n" + "=" * 60)
print("DATA TYPES")
print("=" * 60)

print(df.dtypes)


print("\n" + "=" * 60)
print("MISSING VALUES")
print("=" * 60)

missing = df.isnull().sum()

print(missing[missing > 0].sort_values(ascending=False))


print("\n" + "=" * 60)
print("FIRST 5 ROWS")
print("=" * 60)

print(df.head().to_string())


print("\n" + "=" * 60)
print("BASIC STATISTICS")
print("=" * 60)

print(df.describe().T.to_string())


print("\n" + "=" * 60)
print("INSPECTION COMPLETE")
print("=" * 60)