#!/usr/bin/env python3
"""Deletion test: is the Grad-CAM map faithful to the model? (Petsiuk et al., 2018) - CD-5 interpretability.

    python scripts/xai_deletion.py --model artifacts/ensemble/model.keras --split test --max-images 100

Pixels are removed in Grad-CAM order (most important first) in steps of 5% up to 50%, replaced by a blurred
copy of the image, and the probability of the originally predicted class is recorded. The same is done with a
random order. A faithful map makes the probability fall faster, so its normalised area under the curve (AUC)
is lower; a one-sided Wilcoxon signed-rank test compares the paired AUCs.
Writes <model folder>/reports/xai_deletion/{deletion.csv, deletion.json, deletion.png}.
"""
from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image
from scipy import stats

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import keras  # noqa: E402

from glowrithm_ml.config import load_config, load_json, meta_path_for, save_json  # noqa: E402
from glowrithm_ml.data import load_split  # noqa: E402
from glowrithm_ml.gradcam import GradCAM  # noqa: E402
from glowrithm_ml.preprocessing import to_model_input  # noqa: E402

STEPS = np.linspace(0.0, 0.5, 11)
_trapezoid = getattr(np, "trapezoid", None) or np.trapz


def deletion_curve(model, image: np.ndarray, order: np.ndarray, baseline: np.ndarray, cls: int) -> np.ndarray:
    flat, base = image.reshape(-1, 3), baseline.reshape(-1, 3)
    batch = []
    for fraction in STEPS:
        k = int(round(fraction * len(order)))
        edited = flat.copy()
        edited[order[:k]] = base[order[:k]]
        batch.append(edited.reshape(image.shape))
    return np.asarray(model.predict_on_batch(np.stack(batch)))[:, cls]


def auc(curve: np.ndarray) -> float:
    return float(_trapezoid(curve, STEPS) / STEPS[-1])


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--model", required=True)
    parser.add_argument("--config", default="config.yaml")
    parser.add_argument("--split", default="test")
    parser.add_argument("--max-images", type=int, default=100)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    cfg = load_config(args.config)
    meta = load_json(meta_path_for(args.model))
    names = meta["class_names"]
    paths, labels = load_split(cfg["paths"]["manifest"], args.split, names)
    rng = np.random.default_rng(args.seed)
    if len(paths) > args.max_images:
        keep = rng.choice(len(paths), args.max_images, replace=False)
        paths, labels = paths[keep], labels[keep]
    model = keras.saving.load_model(args.model, compile=False)
    explainer = GradCAM(model)
    out_dir = Path(args.model).parent / "reports" / "xai_deletion"
    out_dir.mkdir(parents=True, exist_ok=True)

    rows, cam_curves, random_curves = [], [], []
    for path, label in zip(paths, labels):
        x = to_model_input(np.asarray(Image.open(path).convert("RGB")), meta["img_size"])
        result = explainer.explain(x[None])
        cls = result["class_index"]
        baseline = cv2.GaussianBlur(x, (0, 0), sigmaX=10)
        cam_curve = deletion_curve(model, x, np.argsort(-result["cam"].reshape(-1), kind="stable"), baseline, cls)
        random_curve = deletion_curve(model, x, rng.permutation(x.shape[0] * x.shape[1]), baseline, cls)
        cam_curves.append(cam_curve)
        random_curves.append(random_curve)
        rows.append({"path": path, "true": names[label], "pred": names[cls],
                     "auc_gradcam": round(auc(cam_curve), 4), "auc_random": round(auc(random_curve), 4)})

    auc_cam = np.array([r["auc_gradcam"] for r in rows])
    auc_random = np.array([r["auc_random"] for r in rows])
    try:
        p_value = float(stats.wilcoxon(auc_cam, auc_random, alternative="less").pvalue)
    except ValueError:  # e.g. every paired difference is zero
        p_value = None
    summary = {"n_images": len(rows), "mean_auc_gradcam": float(auc_cam.mean()), "mean_auc_random": float(auc_random.mean()),
               "share_gradcam_lower": float((auc_cam < auc_random).mean()), "wilcoxon_p_one_sided": p_value,
               "steps": STEPS.tolist(), "mean_curve_gradcam": np.mean(cam_curves, axis=0).tolist(),
               "mean_curve_random": np.mean(random_curves, axis=0).tolist()}
    with open(out_dir / "deletion.csv", "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    save_json(summary, out_dir / "deletion.json")

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(6, 4), dpi=150)
    ax.plot(100 * STEPS, summary["mean_curve_gradcam"], marker="o", color="#E0522B", label="Grad-CAM order")
    ax.plot(100 * STEPS, summary["mean_curve_random"], marker="o", color="#0E5C58", label="random order")
    ax.set(xlabel="Pixels removed (%)", ylabel="Probability of predicted class", ylim=(0, 1),
           title=f"Deletion test (n = {len(rows)})")
    ax.legend()
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(out_dir / "deletion.png")
    print(f"Mean AUC: Grad-CAM {summary['mean_auc_gradcam']:.4f} vs random {summary['mean_auc_random']:.4f}; "
          f"Grad-CAM lower for {summary['share_gradcam_lower']:.0%} of images; Wilcoxon p = {p_value}")
    print(f"Saved {out_dir}")


if __name__ == "__main__":
    main()
