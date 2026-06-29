import pandas as pd
from pathlib import Path


class DataProfiler:

    @staticmethod
    def missing_value_report(df):

        report = pd.DataFrame({
            "column": df.columns,
            "missing_count": df.isna().sum().values,
            "missing_percentage": (
                df.isna().mean() * 100
            ).round(2).values
        })

        return report.sort_values(
            "missing_percentage",
            ascending=False
        )

    @staticmethod
    def numeric_summary(df):

        numeric_cols = df.select_dtypes(include=["number"])

        if numeric_cols.empty:

            return pd.DataFrame({
                "message": [
                    "No numeric columns found in dataset"
                ]
            })

        return numeric_cols.describe().T

    @staticmethod
    def nested_summary(df):

        summary = []

        for col in df.columns:

            non_null = df[col].dropna()

            sample_type = (
                type(non_null.iloc[0]).__name__
                if len(non_null) > 0
                else "None"
            )

            summary.append({
                "column": col,
                "sample_type": sample_type,
                "null_count": int(df[col].isna().sum())
            })

        return pd.DataFrame(summary)

    @staticmethod
    def save_csv(df, path):

        Path(path).parent.mkdir(
            parents=True,
            exist_ok=True
        )

        df.to_csv(path, index=False)