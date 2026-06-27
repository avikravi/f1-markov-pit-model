import pandas as pd
from pathlib import Path

PATH = Path("data/processed/laps_2023.parquet")

df = pd.read_parquet(PATH)

print("=== Shape ===")
print(df.shape)

print("\n=== Columns & Types ===")
print(df.dtypes.to_string())

print("\n=== First 10 Rows ===")
print(df.head(10).to_string())

print("\n=== Numeric Summary ===")
print(df.describe().to_string())

print("\n=== compound value counts ===")
print(df["compound"].value_counts().to_string())

print("\n=== safety_car_status value counts ===")
print(df["safety_car_status"].value_counts().to_string())
