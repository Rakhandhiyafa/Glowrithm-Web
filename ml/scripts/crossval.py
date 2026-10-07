#!/usr/bin/env python3
"""Stratified group k-fold cross-validation (CD-5): accuracy and macro-F1 as mean +/- SD with a 95% CI.

    python scripts/crossval.py --config config.yaml --arch ensemble --folds 5

Folds are built from the train + val images only (the test split stays untouched). Images in one
near-duplicate group always stay in the same fold, as in prepare_dataset.py.
Writes artifacts/cv/<arch>/crossval.json. Fold checkpoints are deleted unless --keep-models is given.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
from scipy import stats
from sklearn.model_selection import StratifiedGroupKFold

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import keras  # noqa: E402
import tensorflow as tf  # noqa: E402

from glowrithm_ml.config import load_config, save_json  # noqa: E402
from glowrithm_ml.data import read_manifest  # noqa: E402
from glowrithm_ml.metrics import compute_metrics  # noqa: E402
from glowrithm_ml.training import run_training  # noqa: E402


def summarise(values: list[float]) -> dict:
    arr = np.asarray(values, dtype=float)
    sd = float(arr.std(ddof=1)) if len(arr) > 1 else 0.0
    half = float(stats.t.ppf(0.975, len(arr) - 1) * sd / np.sqrt(len(arr))) if len(arr) > 1 else 0.0
    return {"mean": float(arr.mean()), "sd": sd, "ci95": [float(arr.mean() - half), float(arr.mean() + half)]}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--config", default="config.yaml")
    parser.add_argument("--arch", default="ensemble", choices=["ensemble", "resnet", "effnet"])
    parser.add_argument("--folds", type=int, default=5)
    parser.add_argument("--weights", help="imagenet | none (default: config)")
    parser.add_argument("--out", help="default: artifacts/cv/<arch>")
    parser.add_argument("--smoke-test", action="store_true")
    parser.add_argument("--keep-models", action="store_true")
    parser.add_argument("--verbose", type=int, default=2, choices=[0, 1, 2])
    args = parser.parse_args()

    cfg = load_config(args.config)
    class_names, seed = cfg["project"]["class_names"], cfg["project"]["seed"]
    weights = args.weights if args.weights is not None else cfg["training"].get("weights", "imagenet")
    weights = None if str(weights).lower() in ("none", "null", "") else weights
    for gpu in tf.config.list_physical_devices("GPU"):
        tf.config.experimental.set_memory_growth(gpu, True)
    base = Path(cfg["paths"]["manifest"]).parent
    rows = [r for r in read_manifest(cfg["paths"]["manifest"]) if r["split"] in ("train", "val")]
    paths = np.array([str(base / r["path"]) for r in rows])
    labels = np.array([class_names.index(r["label"]) for r in rows], dtype=np.int32)
    groups = np.array([r["group"] for r in rows])
    out_dir = Path(args.out) if args.out else Path(cfg["paths"]["artifacts_dir"]) / "cv" / args.arch

    folds = []
    splitter = StratifiedGroupKFold(n_splits=args.folds, shuffle=True, random_state=seed)
    for k, (train_idx, val_idx) in enumerate(splitter.split(paths, labels, groups), 1):
        keras.backend.clear_session()
        keras.utils.set_random_seed(seed + k)
        print(f"\n===== fold {k}/{args.folds}: {len(train_idx)} train / {len(val_idx)} validation images")
        run = run_training(cfg, args.arch, weights, paths[train_idx], labels[train_idx], paths[val_idx],
                           labels[val_idx], out_dir / f"fold_{k}", args.smoke_test, args.verbose)
        metrics = compute_metrics(labels[val_idx], run["model"].predict(run["val_ds"], verbose=0), class_names)
        folds.append({"fold": k, "n_val": int(len(val_idx)), "accuracy": metrics["accuracy"],
                      "macro_f1": metrics["macro"]["f1"]})
        print(f"fold {k}: accuracy {metrics['accuracy']:.4f}  macro-F1 {metrics['macro']['f1']:.4f}")
        if not args.keep_models:
            (out_dir / f"fold_{k}" / "best.keras").unlink(missing_ok=True)

    summary = {m: summarise([f[m] for f in folds]) for m in ("accuracy", "macro_f1")}
    save_json({"arch": args.arch, "folds_k": args.folds, "folds": folds, "summary": summary}, out_dir / "crossval.json")
    for metric, s in summary.items():
        print(f"{metric:<9} {s['mean']:.4f} +/- {s['sd']:.4f} (95% CI {s['ci95'][0]:.4f} - {s['ci95'][1]:.4f})")
    print(f"Saved {out_dir / 'crossval.json'}")


if __name__ == "__main__":
    main()
