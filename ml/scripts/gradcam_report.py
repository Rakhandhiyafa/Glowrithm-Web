#!/usr/bin/env python3
"""Grad-CAM figures for the interpretability analysis (CD-5).

    python scripts/gradcam_report.py --model artifacts/ensemble/model.keras --per-class 3

Uses reports/test/predictions.csv from evaluate.py to pick, per class, the most confident correct
predictions and the misclassified ones. Each row shows: input | one map per backbone | fused overlay.
Writes <model folder>/reports/gradcam/gradcam_<class>.png and individual overlays.
"""
from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import keras  # noqa: E402

from glowrithm_ml.config import load_json, meta_path_for  # noqa: E402
from glowrithm_ml.gradcam import GradCAM, overlay  # noqa: E402
from glowrithm_ml.preprocessing import to_model_input  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--model", required=True)
    parser.add_argument("--predictions", help="default: <model folder>/reports/test/predictions.csv")
    parser.add_argument("--per-class", type=int, default=3)
    args = parser.parse_args()

    meta = load_json(meta_path_for(args.model))
    model_dir = Path(args.model).parent
    pred_file = Path(args.predictions or model_dir / "reports" / "test" / "predictions.csv")
    if not pred_file.exists():
        sys.exit(f"{pred_file} not found - run scripts/evaluate.py first.")
    with open(pred_file, newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))

    out_dir = model_dir / "reports" / "gradcam"
    (out_dir / "overlays").mkdir(parents=True, exist_ok=True)
    explainer = GradCAM(keras.saving.load_model(args.model, compile=False))

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    for cls in meta["class_names"]:
        mine = [r for r in rows if r["true"] == cls]
        correct = sorted((r for r in mine if r["correct"] == "1"), key=lambda r: -float(r["confidence"]))
        wrong = sorted((r for r in mine if r["correct"] == "0"), key=lambda r: -float(r["confidence"]))
        chosen = correct[: args.per_class] + wrong[: args.per_class]
        if not chosen:
            continue
        cols = 2 + len(explainer.branch_names)
        fig, axes = plt.subplots(len(chosen), cols, figsize=(2.6 * cols, 2.7 * len(chosen)), dpi=130, squeeze=False)
        for row_axes, row in zip(axes, chosen):
            rgb = np.asarray(Image.open(row["path"]).convert("RGB"))
            result = explainer.explain(to_model_input(rgb, meta["img_size"])[None])
            panels = [("input", rgb)]
            panels += [(f"{name} map", overlay(rgb, cam)) for name, cam in result["branch_cams"].items()]
            panels.append(("fused Grad-CAM", overlay(rgb, result["cam"])))
            for ax, (title, image) in zip(row_axes, panels):
                ax.imshow(image)
                ax.set_title(title, fontsize=8)
                ax.axis("off")
            verdict = "correct" if row["correct"] == "1" else "WRONG"
            row_axes[0].set_title(f"true {row['true']} / pred {row['pred']} ({float(row['confidence']):.0%}) {verdict}", fontsize=8)
            Image.fromarray(panels[-1][1]).save(out_dir / "overlays" / f"{cls}_{verdict}_{Path(row['path']).stem}.jpg", quality=92)
        fig.tight_layout()
        fig.savefig(out_dir / f"gradcam_{cls}.png")
        plt.close(fig)
        print(f"{cls}: {len(correct[: args.per_class])} correct + {len(wrong[: args.per_class])} misclassified examples")
    print(f"Saved figures to {out_dir}")


if __name__ == "__main__":
    main()
