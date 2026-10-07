#!/usr/bin/env python3
"""Evaluate a trained model on one split and write the CD-5 report files.

    python scripts/evaluate.py --model artifacts/ensemble/model.keras --split test

Writes to <model folder>/reports/<split>/:
  metrics.json, per_class_metrics.csv (TP/FP/FN/TN, precision, recall, F1), classification_report.txt,
  confusion_matrix.png, confusion_matrix_normalized.png, roc_curves.png, predictions.csv
"""
from __future__ import annotations

import argparse
import csv
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import keras  # noqa: E402

from glowrithm_ml.config import load_config, load_json, meta_path_for, save_json  # noqa: E402
from glowrithm_ml.data import load_split, make_eval_dataset  # noqa: E402
from glowrithm_ml.metrics import (compute_metrics, format_summary, plot_confusion_matrix, plot_roc,  # noqa: E402
                                  write_per_class_csv)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--model", required=True)
    parser.add_argument("--config", default="config.yaml")
    parser.add_argument("--split", default="test", choices=["train", "val", "test"])
    parser.add_argument("--out", help="output folder (default: <model folder>/reports/<split>)")
    args = parser.parse_args()

    cfg = load_config(args.config)
    meta = load_json(meta_path_for(args.model))
    class_names = meta["class_names"]
    out_dir = Path(args.out) if args.out else Path(args.model).parent / "reports" / args.split
    out_dir.mkdir(parents=True, exist_ok=True)

    paths, labels = load_split(cfg["paths"]["manifest"], args.split, class_names)
    if len(paths) == 0:
        sys.exit(f"Split '{args.split}' is empty.")
    model = keras.saving.load_model(args.model, compile=False)
    dataset = make_eval_dataset(paths, labels, cfg, img_size=meta["img_size"])
    started = time.perf_counter()
    probs = model.predict(dataset, verbose=0)
    elapsed = time.perf_counter() - started

    metrics = compute_metrics(labels, probs, class_names)
    confidence = probs.max(axis=1)
    threshold = cfg["evaluation"]["low_confidence_threshold"]
    confident = confidence >= threshold
    metrics.update({
        "split": args.split,
        "model_version": meta.get("model_version"),
        "target_accuracy": cfg["evaluation"]["target_accuracy"],
        "meets_target": metrics["accuracy"] >= cfg["evaluation"]["target_accuracy"],
        "low_confidence_threshold": threshold,
        "low_confidence_rate": float((~confident).mean()),
        "accuracy_on_confident": float((probs.argmax(1)[confident] == labels[confident]).mean()) if confident.any() else None,
        "batch_inference_ms_per_image": 1000.0 * elapsed / len(labels),
    })
    save_json(metrics, out_dir / "metrics.json")
    write_per_class_csv(metrics, out_dir / "per_class_metrics.csv")
    (out_dir / "classification_report.txt").write_text(format_summary(metrics) + "\n", encoding="utf-8")
    plot_confusion_matrix(metrics["confusion_matrix"], class_names, out_dir / "confusion_matrix.png")
    plot_confusion_matrix(metrics["confusion_matrix"], class_names, out_dir / "confusion_matrix_normalized.png", normalize=True)
    plot_roc(labels, probs, class_names, out_dir / "roc_curves.png")
    with open(out_dir / "predictions.csv", "w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(["path", "true", "pred", "confidence", "correct"] + [f"p_{c}" for c in class_names])
        for path, y, p in zip(paths, labels, probs):
            pred = int(p.argmax())
            writer.writerow([path, class_names[y], class_names[pred], f"{p[pred]:.4f}", int(pred == y)]
                            + [f"{v:.4f}" for v in p])

    print(format_summary(metrics))
    verdict = "MEETS" if metrics["meets_target"] else "DOES NOT MEET"
    print(f"\nAccuracy {metrics['accuracy']:.2%} {verdict} the CD-3 target of {metrics['target_accuracy']:.0%}.")
    low, high = metrics["accuracy_ci95"]
    print(f"95% Wilson interval of the accuracy: {low:.2%} - {high:.2%}")
    print(f"Low-confidence predictions (<{threshold:.0%}): {metrics['low_confidence_rate']:.1%}")
    print(f"Reports written to {out_dir}")


if __name__ == "__main__":
    main()
