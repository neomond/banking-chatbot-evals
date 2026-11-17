"""Measure how well the LLM judge agrees with human reviewers.

1. Run:  python -m evals.runner --bot llm --judge --out reports/llm
2. Label a sample by hand in data/human_labels.csv (copy the template; 20-30 rows is enough to start):
       case_id,criterion,human_score
3. Run:  python scripts/calibrate_judge.py reports/llm.json data/human_labels.csv

Scores are bucketed to pass (>=4) / fail (<=3) before computing Cohen's kappa, because
agreement on the decision matters more than exact 1-5 matches. Rule of thumb: kappa >= 0.6
before you let a judge criterion influence the release gate.
"""
from __future__ import annotations

import csv
import json
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from evals.stats import cohen_kappa  # noqa: E402


def main(results_path: str, labels_path: str) -> None:
    results = {r["id"]: r for r in json.loads(Path(results_path).read_text(encoding="utf-8"))["results"]}
    pairs = defaultdict(lambda: ([], []))
    with open(labels_path, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            r = results.get(row["case_id"])
            judge_scores = (r or {}).get("judge", {}).get("scores", {})
            if row["criterion"] not in judge_scores:
                continue
            h, j = pairs[row["criterion"]]
            h.append(int(row["human_score"]) >= 4)
            j.append(int(judge_scores[row["criterion"]]) >= 4)
    if not pairs:
        sys.exit("No overlapping labels: did you run the judge and fill in human_labels.csv?")
    print("criterion        n   agreement  kappa")
    for crit, (h, j) in sorted(pairs.items()):
        agree = sum(x == y for x, y in zip(h, j)) / len(h)
        print(f"{crit:<15} {len(h):>3}   {agree:>8.0%}  {cohen_kappa(h, j):>5.2f}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    main(sys.argv[1], sys.argv[2])
