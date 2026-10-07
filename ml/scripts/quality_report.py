#!/usr/bin/env python3
"""Calibrate the quality-gate thresholds on your own data.

    python scripts/quality_report.py --config config.yaml --split train

Prints percentiles of brightness, glare and sharpness over the processed face crops and the share of images
the current thresholds would reject. If many good training photos would fail, loosen that threshold to about
their 1st-5th percentile in glowrithm_ml/quality.py, and report the final values in CD-4.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from glowrithm_ml.config import load_config, save_json  # noqa: E402
from glowrithm_ml.data import read_manifest  # noqa: E402
from glowrithm_ml.quality import QualityThresholds, measure  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--config", default="config.yaml")
    parser.add_argument("--split", default="train", choices=["train", "val", "test", "all"])
    args = parser.parse_args()

    cfg = load_config(args.config)
    base = Path(cfg["paths"]["manifest"]).parent
    rows = [r for r in read_manifest(cfg["paths"]["manifest"]) if args.split == "all" or r["split"] == args.split]
    if not rows:
        sys.exit("No images found for this split.")
    values: dict[str, list[float]] = {"brightness": [], "glare": [], "sharpness": []}
    for row in rows:
        measured = measure(np.asarray(Image.open(base / row["path"]).convert("RGB")))
        for key in values:
            values[key].append(measured[key])
    t = QualityThresholds()
    failing = {
        "brightness": lambda a: (a < t.brightness_fail[0]) | (a > t.brightness_fail[1]),
        "glare": lambda a: a > t.glare_fail,
        "sharpness": lambda a: a < t.sharpness_fail,
    }
    report = {"split": args.split, "n_images": len(rows)}
    print(f"{len(rows)} images ({args.split})\n{'metric':<11}{'p1':>9}{'p5':>9}{'p50':>9}{'p95':>9}{'p99':>9}  fail share")
    for key, vals in values.items():
        arr = np.asarray(vals)
        pct = {f"p{p}": float(np.percentile(arr, p)) for p in (1, 5, 50, 95, 99)}
        share = float(failing[key](arr).mean())
        report[key] = {"percentiles": pct, "share_failing_current_threshold": share}
        print(f"{key:<11}" + "".join(f"{v:>9.3f}" for v in pct.values()) + f"  {share:.1%}")
    out = Path(cfg["paths"]["manifest"]).with_name("quality_report.json")
    save_json(report, out)
    print(f"Saved {out}")


if __name__ == "__main__":
    main()
