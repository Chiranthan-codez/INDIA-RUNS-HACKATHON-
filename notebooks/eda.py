import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

from src.preprocessing.loader import DatasetLoader
from src.preprocessing.schema_inspector import SchemaInspector
from src.preprocessing.profiler import DataProfiler


# Dataset file
DATA_FILE = "candidates.jsonl"

# Create loader
loader = DatasetLoader("data/raw")

# Load dataset
df = loader.auto_load(DATA_FILE)

print("=" * 50)
print("DATASET SHAPE")
print(df.shape)

print("=" * 50)
print("COLUMNS")
print(df.columns.tolist())

print("=" * 50)
print("COLUMN TYPES")

for col in df.columns:
    sample = df[col].dropna()

    if len(sample) > 0:
        print(f"{col}: {type(sample.iloc[0]).__name__}")
    else:
        print(f"{col}: Empty")

# -----------------------
# Schema inspection
# -----------------------
schema = SchemaInspector.inspect(df)

SchemaInspector.save(
    schema,
    "outputs/schema_report.json"
)

# -----------------------
# Missing value report
# -----------------------
@staticmethod
def missing_value_report(df):

    import pandas as pd

    report = []

    for col in df.columns:

        null_count = 0
        empty_count = 0

        for value in df[col]:

            if pd.isna(value):
                null_count += 1

            elif isinstance(value, (list, dict)) and len(value) == 0:
                empty_count += 1

        report.append({
            "column": col,
            "null_count": null_count,
            "empty_objects": empty_count,
            "missing_percentage": round(
                ((null_count + empty_count) / len(df)) * 100,
                2
            )
        })

    return pd.DataFrame(report)
# -----------------------
# Numeric summary
# -----------------------
numeric_summary = DataProfiler.numeric_summary(df)

numeric_summary.to_csv(
    "outputs/column_stats.csv",
    index=False
)

# -----------------------
# Nested data summary
# -----------------------
if hasattr(DataProfiler, "nested_summary"):

    nested_summary = DataProfiler.nested_summary(df)

    nested_summary.to_csv(
        "outputs/nested_summary.csv",
        index=False
    )

    print("=" * 50)
    print("NESTED SUMMARY")
    print(nested_summary)

print("=" * 50)
print("EDA COMPLETE")
print("\nSAMPLE RECORD\n")

for col in df.columns:

    value = df[col].iloc[0]

    print(f"{col}")

    print(f"type: {type(value).__name__}")

    if isinstance(value, dict):
        print("keys:", list(value.keys()))

    elif isinstance(value, list):
        print(f"items: {len(value)}")

    print("-" * 40)