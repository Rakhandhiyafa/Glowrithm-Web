#!/usr/bin/env python3
"""Train the Glowrithm skin-type classifier (two-phase transfer learning, see glowrithm_ml/training.py).

Phase 1 (head)      : both backbones frozen, only the fusion head learns (Adam, lr 1e-3).
Phase 2 (fine-tune) : the top `unfreeze_fraction` of each backbone is unfrozen (BatchNorm stays frozen) and the
                      network is trained with a small learning rate (1e-5).
The checkpoint with the best validation macro-F1 over both phases is exported as model.keras.

    python scripts/train.py --config config.yaml                 # ensemble ResNet50V2 + EfficientNetB0
    python scripts/train.py --config config.yaml --arch resnet   # single-backbone baseline (ablation)
    python scripts/train.py --config config.yaml --arch effnet   # single-backbone baseline (ablation)
    python scripts/train.py --config config.yaml --smoke-test    # 1 short epoch per phase: pipeline check

Outputs in artifacts/<arch>/: model.keras, model_meta.json, history.csv, training_curves.png, model_summary.txt
"""
from __future__ import annotations

import argparse
import platform
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import keras  # noqa: E402
import tensorflow as tf  # noqa: E402

from glowrithm_ml.config import load_config, save_json  # noqa: E402
from glowrithm_ml.data import count_per_class, load_split  # noqa: E402
from glowrithm_ml.metrics import compute_metrics, format_summary, merge_histories, plot_history  # noqa: E402
from glowrithm_ml.training import run_training  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--config", default="config.yaml")
    parser.add_argument("--arch", choices=["ensemble", "resnet", "effnet"], help="override training.arch")
    parser.add_argument("--weights", help="override training.weights: imagenet | none")
    parser.add_argument("--out", help="output folder (default: artifacts/<arch>)")
    parser.add_argument("--smoke-test", action="store_true", help="1 epoch per phase, 2 steps each")
    parser.add_argument("--verbose", type=int, default=2, choices=[0, 1, 2])
    args = parser.parse_args()

    cfg = load_config(args.config)
    tcfg, dcfg = cfg["training"], cfg["data"]
    arch = args.arch or tcfg["arch"]
    weights = args.weights if args.weights is not None else tcfg.get("weights", "imagenet")
    weights = None if str(weights).lower() in ("none", "null", "") else weights
    class_names = cfg["project"]["class_names"]
    keras.utils.set_random_seed(cfg["project"]["seed"])
    for gpu in tf.config.list_physical_devices("GPU"):
        tf.config.experimental.set_memory_growth(gpu, True)

    out_dir = Path(args.out) if args.out else Path(cfg["paths"]["artifacts_dir"]) / arch
    x_train, y_train = load_split(cfg["paths"]["manifest"], "train", class_names)
    x_val, y_val = load_split(cfg["paths"]["manifest"], "val", class_names)
    if len(x_train) == 0 or len(x_val) == 0:
        sys.exit("The train/val split is empty - run scripts/prepare_dataset.py first.")
    train_counts = dict(zip(class_names, count_per_class(y_train, len(class_names)).tolist()))
    val_counts = dict(zip(class_names, count_per_class(y_val, len(class_names)).tolist()))
    print(f"Train images per class: {train_counts}\nVal images per class:   {val_counts}")

    run = run_training(cfg, arch, weights, x_train, y_train, x_val, y_val, out_dir, args.smoke_test, args.verbose)
    best = run["model"]
    best.save(out_dir / "model.keras")
    val_metrics = compute_metrics(y_val, best.predict(run["val_ds"], verbose=0), class_names)
    meta = {
        "model_version": f"{arch}-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M')}",
        "arch": arch,
        "backbones": run["backbones"],
        "class_names": class_names,
        "img_size": dcfg["img_size"],
        "processed_size": dcfg["processed_size"],
        "crop_faces": dcfg["crop_faces"],
        "face_margin": dcfg["face_margin"],
        "input": "RGB float32 in [0, 255], shape (N, img_size, img_size, 3)",
        "weights_init": weights or "random",
        "params": {"total": run["trainable"] + run["frozen"], "trainable_finetune": run["trainable"],
                   "frozen_finetune": run["frozen"]},
        "train_counts": train_counts,
        "val_counts": val_counts,
        "val_metrics": {"accuracy": val_metrics["accuracy"], "macro_f1": val_metrics["macro"]["f1"]},
        "epochs_run": {"head": run["epochs_head"], "finetune": run["epochs_finetune"]},
        "training_seconds": round(run["seconds"], 1),
        "versions": {"tensorflow": tf.__version__, "keras": keras.__version__, "python": platform.python_version()},
        "config": {key: cfg[key] for key in ("data", "augmentation", "training")},
        "created_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    save_json(meta, out_dir / "model_meta.json")
    history = merge_histories([out_dir / "history_head.csv", out_dir / "history_finetune.csv"], out_dir / "history.csv")
    plot_history(history, out_dir / "training_curves.png", finetune_start=run["finetune_start"])
    print("\nValidation results of the exported model:\n" + format_summary(val_metrics))
    print(f"\nSaved {out_dir / 'model.keras'} ({run['seconds'] / 60:.1f} min of training)")


if __name__ == "__main__":
    main()
