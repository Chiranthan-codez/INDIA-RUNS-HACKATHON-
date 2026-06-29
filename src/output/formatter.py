import csv
from pathlib import Path
from typing import List


class SubmissionFormatter:
    """
    Writes the final ranked candidates to a CSV file matching the exact
    submission spec: candidate_id, rank, score, reasoning.

    Validates:
        - Exactly 100 data rows.
        - Ranks 1-100 each used exactly once.
        - Scores are monotonically non-increasing.

    Complexity: O(N) where N = 100.
    """

    HEADER = ["candidate_id", "rank", "score", "reasoning"]

    def write_csv(self, ranked: List[dict], output_path: str) -> None:
        """
        Writes the ranked list to CSV.

        Args:
            ranked: List of dicts with keys: candidate_id, rank, score, reasoning.
            output_path: Path to the output CSV file.
        """
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(self.HEADER)

            for entry in ranked:
                writer.writerow([
                    entry["candidate_id"],
                    entry["rank"],
                    f'{entry["score"]:.4f}',
                    entry["reasoning"],
                ])

    def validate(self, output_path: str) -> List[str]:
        """
        Basic pre-submission validation.
        Returns a list of error strings (empty = valid).
        """
        errors = []
        path = Path(output_path)

        if not path.exists():
            errors.append(f"File not found: {output_path}")
            return errors

        with open(path, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            header = next(reader, None)

            if header != self.HEADER:
                errors.append(f"Header mismatch: expected {self.HEADER}, got {header}")

            rows = [row for row in reader if any(cell.strip() for cell in row)]

        if len(rows) != 100:
            errors.append(f"Expected 100 data rows, got {len(rows)}")

        # Check ranks
        ranks = set()
        prev_score = float("inf")

        for i, row in enumerate(rows):
            if len(row) != 4:
                errors.append(f"Row {i+2}: expected 4 columns, got {len(row)}")
                continue

            try:
                rank = int(row[1])
                score = float(row[2])
            except ValueError:
                errors.append(f"Row {i+2}: rank/score parsing error")
                continue

            if rank in ranks:
                errors.append(f"Row {i+2}: duplicate rank {rank}")
            ranks.add(rank)

            if score > prev_score:
                errors.append(f"Row {i+2}: score {score} > previous {prev_score} (not non-increasing)")
            prev_score = score

        missing = set(range(1, 101)) - ranks
        if missing:
            errors.append(f"Missing ranks: {sorted(missing)}")

        return errors
