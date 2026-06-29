from pathlib import Path
import pandas as pd


class DatasetLoader:

    def __init__(self, data_dir: str):
        self.data_dir = Path(data_dir)

    def load_csv(self, filename: str) -> pd.DataFrame:
        path = self.data_dir / filename

        if not path.exists():
            raise FileNotFoundError(f"{path} not found")

        return pd.read_csv(path)

    def load_parquet(self, filename: str) -> pd.DataFrame:
        path = self.data_dir / filename

        if not path.exists():
            raise FileNotFoundError(f"{path} not found")

        return pd.read_parquet(path)

    def load_jsonl(self, filename: str) -> pd.DataFrame:
        path = self.data_dir / filename

        if not path.exists():
            raise FileNotFoundError(f"{path} not found")

        return pd.read_json(path, lines=True)

    def auto_load(self, filename: str) -> pd.DataFrame:

        if filename.endswith(".csv"):
            return self.load_csv(filename)

        elif filename.endswith(".parquet"):
            return self.load_parquet(filename)

        elif filename.endswith(".jsonl"):
            return self.load_jsonl(filename)

        raise ValueError("Unsupported file type")