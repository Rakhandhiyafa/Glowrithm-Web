#!/usr/bin/env python3
"""Statistical comparison of two models on the same test images (CD-5 ablation test).

    python scripts/compare_models.py artifacts/ensemble/reports/test/predictions.csv \
        artifacts/effnet/reports/test/predictions.csv --names ensemble effnet

McNemar's test uses only the images the two models classify differently:
  b = images model A gets right and model B gets wrong, c = the opposite;
  b + c < 25 -> exact binomial test, otherwise chi2 = (|b - c| - 1)^2 / (b + c) with 1 degree of freedom.
Also reports each model's accuracy with a 95% Wilson interval and a bootstrap 95% CI of the macro-F1 difference.
"""
from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

import numpy as np
from scipy import stats
from sklearn.metrics import f1_score

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from glowrithm_ml.config import save_json  # noqa: E402
from glowrithm_ml.metrics import wilson_interval  # noqa: E402


def read_predictions(path) -> dict[str, dict]:
    with open(path, newline="", encoding="utf-8") as fh:
        return {row["path"]: row for row in csv.DictReader(fh)}


def mcnemar(b: int, c: int) -> dict:
    """McNemar's test on the discordant pairs b and c."""
    n = b + c
    if n == 0:
        return {"b": b, "c": c, "method": "no discordant pairs", "statistic": None, "p_value": 1.0}
    if n < 25:
        p_value = stats.binomtest(min(b, c), n, 0.5).pvalue
        return {"b": b, "c": c, "method": "exact binomial", "statistic": None, "p_value": float(p_value)}
    chi2 = (abs(b - c) - 1) ** 2 / n
    return {"b": b, "c": c, "method": "chi-square, continuity corrected", "statistic": float(chi2),
            "p_value": float(stats.chi2.sf(chi2, df=1))}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("pred_a")
    parser.add_argument("pred_b")
    parser.add_argument("--names", nargs=2, default=["A", "B"])
    parser.add_argument("--bootstrap", type=int, default=2000)
    parser.add_argument("--out", help="JSON report (default: compare_<A>_vs_<B>.json next to pred_a)")
    args = parser.parse_args()

    rows_a, rows_b = read_predictions(args.pred_a), read_predictions(args.pred_b)
    keys = sorted(set(rows_a) & set(rows_b))
    if not keys:
        sys.exit("The two prediction files have no images in common.")
    y = np.array([rows_a[k]["true"] for k in keys])
    pred_a = np.array([rows_a[k]["pred"] for k in keys])
    pred_b = np.array([rows_b[k]["pred"] for k in keys])
    right_a, right_b = pred_a == y, pred_b == y
    test = mcnemar(int(np.sum(right_a & ~right_b)), int(np.sum(~right_a & right_b)))

    labels = sorted(set(y))
    f1 = lambda pred, idx=slice(None): f1_score(y[idx], pred[idx], labels=labels, average="macro", zero_division=0)  # noqa: E731
    rng = np.random.default_rng(42)
    diffs = []
    for _ in range(args.bootstrap):
        idx = rng.integers(0, len(y), len(y))
        diffs.append(f1(pred_a, idx) - f1(pred_b, idx))
    name_a, name_b = args.names
    report = {
        "n_images": len(keys),
        name_a: {"accuracy": float(right_a.mean()), "accuracy_ci95": wilson_interval(int(right_a.sum()), len(keys)),
                 "macro_f1": float(f1(pred_a))},
        name_b: {"accuracy": float(right_b.mean()), "accuracy_ci95": wilson_interval(int(right_b.sum()), len(keys)),
                 "macro_f1": float(f1(pred_b))},
        "mcnemar": test,
        "macro_f1_difference": {"estimate": float(f1(pred_a) - f1(pred_b)),
                                "ci95_bootstrap": [float(np.percentile(diffs, 2.5)), float(np.percentile(diffs, 97.5))]},
        "significant_at_0_05": test["p_value"] < 0.05,
    }
    out = Path(args.out) if args.out else Path(args.pred_a).with_name(f"compare_{name_a}_vs_{name_b}.json")
    save_json(report, out)
    for name in (name_a, name_b):
        lo, hi = report[name]["accuracy_ci95"]
        print(f"{name:<10} accuracy {report[name]['accuracy']:.4f} (95% CI {lo:.4f}-{hi:.4f})  macro-F1 {report[name]['macro_f1']:.4f}")
    d = report["macro_f1_difference"]
    print(f"McNemar ({test['method']}): b={test['b']} c={test['c']} p={test['p_value']:.4g}")
    print(f"macro-F1 difference {d['estimate']:+.4f} (bootstrap 95% CI {d['ci95_bootstrap'][0]:+.4f} to {d['ci95_bootstrap'][1]:+.4f})")
    print("Significant at 0.05" if report["significant_at_0_05"] else "Not significant at 0.05: prefer the lighter model")
    print(f"Saved {out}")


if __name__ == "__main__":
    main()
