#!/usr/bin/env python3
"""System Usability Scale (SUS) calculator for the CD-5 usability test.

    python scripts/sus_score.py responses.csv

CSV header: respondent,q1,q2,...,q10 with Likert answers 1 (strongly disagree) .. 5 (strongly agree).
SUS_i = 2.5 * [ sum_odd (q - 1) + sum_even (5 - q) ]  ->  0..100 per respondent; report the mean.
Interpretation: 68 is the average SUS score; Bangor et al. acceptability: < 50 not acceptable,
50-70 marginal, > 70 acceptable.
"""
from __future__ import annotations

import csv
import statistics
import sys


def sus(answers: list[int]) -> float:
    if len(answers) != 10 or any(a not in (1, 2, 3, 4, 5) for a in answers):
        raise ValueError(f"expected ten answers between 1 and 5, got {answers}")
    odd = sum(answers[i] - 1 for i in range(0, 10, 2))
    even = sum(5 - answers[i] for i in range(1, 10, 2))
    return 2.5 * (odd + even)


def acceptability(score: float) -> str:
    return "acceptable" if score > 70 else "marginal" if score >= 50 else "not acceptable"


def main() -> None:
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    with open(sys.argv[1], newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    scores = []
    for row in rows:
        score = sus([int(row[f"q{i}"]) for i in range(1, 11)])
        scores.append(score)
        print(f"{row.get('respondent', len(scores)):<14} SUS = {score:5.1f}")
    mean = statistics.mean(scores)
    spread = statistics.stdev(scores) if len(scores) > 1 else 0.0
    print(f"\nRespondents: {len(scores)}   mean SUS = {mean:.1f}   SD = {spread:.1f}")
    print(f"Acceptability: {acceptability(mean)}   ({'above' if mean > 68 else 'at or below'} the average of 68)")


if __name__ == "__main__":
    main()
