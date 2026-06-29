import gzip
import json
from pathlib import Path
from typing import Iterator, List
from src.ingestion.candidate_model import Candidate

class CandidateLoader:
    """
    Handles streaming ingestion of candidate records from disk to minimize memory consumption.
    Supports JSONL and gzipped JSONL (.gz).
    """
    def __init__(self, raw_data_path: str):
        self.path = Path(raw_data_path)
        if not self.path.exists():
            raise FileNotFoundError(f"Data file not found at {self.path}")

    def stream(self) -> Iterator[Candidate]:
        """
        Streams candidate profiles one line at a time from file.
        Yields Candidate Pydantic objects.
        """
        open_func = gzip.open if self.path.suffix == ".gz" or self.path.name.endswith(".jsonl.gz") else open
        mode = "rt" if open_func == gzip.open else "r"
        
        with open_func(self.path, mode, encoding="utf-8") as f:
            for line in f:
                line_str = line.strip()
                if not line_str:
                    continue
                record = json.loads(line_str)
                yield Candidate(**record)

    def load_batch(self, limit: int = 0) -> List[Candidate]:
        """
        Loads candidate profiles into memory up to an optional limit.
        """
        candidates = []
        for i, cand in enumerate(self.stream()):
            if limit > 0 and i >= limit:
                break
            candidates.append(cand)
        return candidates
