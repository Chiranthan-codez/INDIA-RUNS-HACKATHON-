import json
from pathlib import Path


class SchemaInspector:

    @staticmethod
    def inspect(df):

        schema = {
            "rows": len(df),
            "columns": len(df.columns),
            "column_details": {}
        }

        for col in df.columns:

            # Handle nested objects safely
            try:
                unique_count = int(df[col].nunique(dropna=True))
            except TypeError:
                unique_count = "complex_object"

            schema["column_details"][col] = {
                "dtype": str(df[col].dtype),
                "null_count": int(df[col].isna().sum()),
                "null_percentage": round(
                    float(df[col].isna().mean() * 100),
                    2
                ),
                "unique_values": unique_count
            }

        return schema

    @staticmethod
    def save(schema, output_path):

        Path(output_path).parent.mkdir(
            parents=True,
            exist_ok=True
        )

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(schema, f, indent=4)