"""
Output Module — CSV formatter and validation helper.

Responsibilities:
- Write the final ranking to a CSV file matching the exact schema requirements
- Validate that the file complies with submission constraints (100 rows, unique ranks, scores monotonically non-increasing)

Boundary contract:
- Exposes: SubmissionFormatter.write_csv(ranked_list, path)
- Exposes: SubmissionFormatter.validate(path) -> list[str] (errors)
- Depends on: nothing in src/
"""
