#!/usr/bin/env python3
"""Quick training without a GPU: frozen ImageNet backbones with cached features (phase 1 of train.py only).

For initial tests on a CPU. Each backbone runs once per image (training images also in --views augmented
versions), the global-average-pooled features are cached, and the classification head of model.py
(Dropout 0.4, Dense 256 ReLU + L2, Dropout 0.3, Dense 3) is trained on them for every architecture:
ensemble (ResNet50V2 + EfficientNetB0 features concatenated), resnet and effnet. Each trained head is put back
on its frozen backbones and saved as an ordinary model.keras + model_meta.json, so evaluate.py, the other
report scripts, the backend and the web app use it unchanged. Fine-tuning (phase 2) is not done here: use
train.py on a GPU for the final model.

    python scripts/train_cached.py --config config.yaml --views 4

Writes artifacts/<arch>/{model.keras, model_meta.json, history.csv, training_curves.png} for each architecture,
and artifacts/cached/: features.npz, cv_heads.json (5-fold group cross-validation of each head on the
train+val features) and nearest_neighbours.json (cosine similarity of each test image to its closest training
image, a leakage check).
"""
from __future__ import annotations

import argparse
import csv
import platform
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import keras  # noqa: E402
import tensorflow as tf  # noqa: E402
from keras import layers  # noqa: E402
from sklearn.model_selection import StratifiedGroupKFold  # noqa: E402

from glowrithm_ml.config import load_config, save_json  # noqa: E402
from glowrithm_ml.data import _loader, build_augmenter, class_weights, read_manifest  # noqa: E402
from glowrithm_ml.metrics import compute_metrics, format_summary, plot_history  # noqa: E402
from glowrithm_ml.model import build_model  # noqa: E402

ARCHS = {"ensemble": ("resnet", "effnet"), "resnet": ("resnet",), "effnet": ("effnet",)}


def split_rows(manifest: str, split: str, class_names: list[str]) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    base = Path(manifest).parent
    rows = [r for r in read_manifest(manifest) if r["split"] == split]
    return (np.array([str(base / r["path"]) for r in rows]), np.array([class_names.index(r["label"]) for r in rows]),
            np.array([r["group"] for r in rows]))


def extract(feature_model, paths: np.ndarray, cfg: dict, augmenter=None, batch: int = 32) -> dict[str, np.ndarray]:
    load = _loader(cfg["data"]["img_size"], len(cfg["project"]["class_names"]))
    ds = tf.data.Dataset.from_tensor_slices((paths, np.zeros(len(paths), np.int32))).map(load).batch(batch)
    outs = {"resnet": [], "effnet": []}
    for x, _ in ds:
        if augmenter is not None:
            x = tf.clip_by_value(augmenter(x, training=True), 0.0, 255.0)
        resnet, effnet = feature_model(x, training=False)
        outs["resnet"].append(np.asarray(resnet, np.float32))
        outs["effnet"].append(np.asarray(effnet, np.float32))
    return {k: np.concatenate(v) for k, v in outs.items()}


def features_for(arch: str, feats: dict[str, np.ndarray]) -> np.ndarray:
    return np.concatenate([feats[b] for b in ARCHS[arch]], axis=1)


def build_head(dim: int, tcfg: dict, n_classes: int, arch: str) -> keras.Model:
    """The same layers (and names) as the top of model.build_model, so the weights transfer by name."""
    inputs = keras.Input((dim,), name="features")
    x = layers.Dropout(tcfg["dropout_1"], name="dropout_1")(inputs)
    x = layers.Dense(tcfg["dense_units"], activation="relu", kernel_regularizer=keras.regularizers.l2(tcfg["l2"]), name="fc")(x)
    x = layers.Dropout(tcfg["dropout_2"], name="dropout_2")(x)
    logits = layers.Dense(n_classes, name="logits")(x)
    probs = layers.Activation("softmax", dtype="float32", name="probs")(logits)
    return keras.Model(inputs, probs, name=f"head_{arch}")


def train_head(x_tr, y_tr, x_va, y_va, tcfg: dict, n_classes: int, arch: str, seed: int, log_path=None,
               max_epochs: int = 150, verbose: int = 0):
    keras.utils.set_random_seed(seed)
    head = build_head(x_tr.shape[1], tcfg, n_classes, arch)
    head.compile(optimizer=keras.optimizers.Adam(tcfg["head"]["learning_rate"]),
                 loss=keras.losses.CategoricalCrossentropy(label_smoothing=tcfg["label_smoothing"]),
                 metrics=["accuracy", keras.metrics.F1Score(average="macro", name="macro_f1")])
    callbacks = [keras.callbacks.EarlyStopping(monitor="val_macro_f1", mode="max", patience=15, restore_best_weights=True),
                 keras.callbacks.ReduceLROnPlateau(monitor="val_loss", factor=0.3, patience=5, min_lr=1e-6)]
    if log_path:
        callbacks.append(keras.callbacks.CSVLogger(str(log_path)))
    weights = class_weights(y_tr, n_classes) if tcfg.get("balance_strategy", "oversample") != "none" else None
    history = head.fit(x_tr, np.eye(n_classes, dtype=np.float32)[y_tr], validation_data=(x_va, np.eye(n_classes, dtype=np.float32)[y_va]),
                       epochs=max_epochs, batch_size=64, class_weight=weights, callbacks=callbacks, verbose=verbose)
    return head, history.history


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--config", default="config.yaml")
    parser.add_argument("--views", type=int, default=4, help="feature copies per training image (1 = no augmentation)")
    parser.add_argument("--archs", nargs="+", default=list(ARCHS), choices=list(ARCHS))
    parser.add_argument("--folds", type=int, default=5, help="cross-validation folds for the heads (0 = skip)")
    parser.add_argument("--reuse-features", action="store_true", help="reuse artifacts/cached/features.npz")
    args = parser.parse_args()

    cfg = load_config(args.config)
    tcfg, dcfg = cfg["training"], cfg["data"]
    class_names, seed = cfg["project"]["class_names"], cfg["project"]["seed"]
    n_classes = len(class_names)
    weights = tcfg.get("weights", "imagenet")
    effnet_file = tcfg.get("effnet_weights_file")
    keras.utils.set_random_seed(seed)
    artifacts = Path(cfg["paths"]["artifacts_dir"])
    cache_dir = artifacts / "cached"
    cache_dir.mkdir(parents=True, exist_ok=True)
    data = {s: split_rows(cfg["paths"]["manifest"], s, class_names) for s in ("train", "val", "test")}
    for s, (p, y, _) in data.items():
        print(f"{s:<5} {len(p):5d} images  per class {np.bincount(y, minlength=n_classes).tolist()}")

    # ---- 1. features of the frozen backbones -------------------------------------------------------
    cache = cache_dir / "features.npz"
    started = time.time()
    if args.reuse_features and cache.exists():
        stored = np.load(cache)
        feats = {key: stored[key] for key in stored.files}
        print(f"Reusing {cache}")
    else:
        full, _ = build_model("ensemble", n_classes, dcfg["img_size"], weights, tcfg["resnet_variant"], tcfg["effnet_variant"],
                              effnet_weights_file=effnet_file)
        feature_model = keras.Model(full.inputs, [full.get_layer("resnet_gap").output, full.get_layer("effnet_gap").output])
        augmenter = build_augmenter(cfg.get("augmentation", {}), seed)
        feats = {}
        for split in ("train", "val", "test"):
            paths = data[split][0]
            views = args.views if split == "train" else 1
            for v in range(views):
                t0 = time.time()
                out = extract(feature_model, paths, cfg, augmenter if v > 0 else None)
                for backbone, array in out.items():
                    feats[f"{split}_v{v}_{backbone}"] = array
                print(f"features {split} view {v + 1}/{views}: {len(paths)} images in {time.time() - t0:.0f} s "
                      f"({len(paths) / max(1e-6, time.time() - t0):.1f} img/s)")
        np.savez(cache, **feats)
    feature_seconds = time.time() - started

    def split_features(split: str, arch: str, all_views: bool) -> np.ndarray:
        views = sorted({int(k.split("_v")[1].split("_")[0]) for k in feats if k.startswith(f"{split}_v")})
        chosen = views if all_views else [0]
        return np.concatenate([features_for(arch, {b: feats[f"{split}_v{v}_{b}"] for b in ("resnet", "effnet")}) for v in chosen])

    n_views = len({k.split("_")[1] for k in feats if k.startswith("train_v")})
    y_train_views = np.tile(data["train"][1], n_views)

    # ---- 2. leakage check: nearest training image of every test image (ensemble features) -------------
    def unit(a):
        return a / np.maximum(np.linalg.norm(a, axis=1, keepdims=True), 1e-12)
    sims = unit(split_features("test", "ensemble", False)) @ unit(split_features("train", "ensemble", False)).T
    nearest = sims.max(axis=1)
    nn_index = sims.argmax(axis=1)
    pairs = sorted(zip(nearest.tolist(), data["test"][0].tolist(), data["train"][0][nn_index].tolist()), reverse=True)
    save_json({"note": "cosine similarity of each test image to its most similar training image (frozen ensemble features)",
               "quantiles": {q: float(np.quantile(nearest, q)) for q in (0.5, 0.9, 0.99, 1.0)},
               "share_above": {t: float(np.mean(nearest > t)) for t in (0.95, 0.97, 0.99)},
               "top_pairs": [{"similarity": round(s, 4), "test": Path(a).name, "train": Path(b).name} for s, a, b in pairs[:20]]},
              cache_dir / "nearest_neighbours.json")
    print(f"Leakage check: test images with a training image at cosine similarity > 0.97: {np.mean(nearest > 0.97):.1%}")

    # ---- 3. heads: cross-validation, then final training per architecture ----------------------------
    cv_report = {}
    if args.folds and args.folds > 1:
        x_groups = np.concatenate([data["train"][2], data["val"][2]])
        y_all = np.concatenate([data["train"][1], data["val"][1]])
        for arch in args.archs:
            x_all = np.concatenate([split_features("train", arch, False), split_features("val", arch, False)])
            folds = []
            splitter = StratifiedGroupKFold(n_splits=args.folds, shuffle=True, random_state=seed)
            for k, (tr, va) in enumerate(splitter.split(x_all, y_all, x_groups), 1):
                head, _ = train_head(x_all[tr], y_all[tr], x_all[va], y_all[va], tcfg, n_classes, arch, seed + k)
                m = compute_metrics(y_all[va], head.predict(x_all[va], verbose=0), class_names)
                folds.append({"fold": k, "n_val": int(len(va)), "accuracy": m["accuracy"], "macro_f1": m["macro"]["f1"]})
            acc = np.array([f["accuracy"] for f in folds])
            f1 = np.array([f["macro_f1"] for f in folds])
            cv_report[arch] = {"folds": folds, "accuracy_mean": float(acc.mean()), "accuracy_sd": float(acc.std(ddof=1)),
                               "macro_f1_mean": float(f1.mean()), "macro_f1_sd": float(f1.std(ddof=1))}
            print(f"CV {arch:<8} accuracy {acc.mean():.4f} +/- {acc.std(ddof=1):.4f}   macro-F1 {f1.mean():.4f} +/- {f1.std(ddof=1):.4f}")
        save_json({"method": f"{args.folds}-fold StratifiedGroupKFold on train+val, original views, frozen features",
                   "results": cv_report}, cache_dir / "cv_heads.json")

    for arch in args.archs:
        out_dir = artifacts / arch
        out_dir.mkdir(parents=True, exist_ok=True)
        t0 = time.time()
        x_tr, x_va = split_features("train", arch, True), split_features("val", arch, False)
        head, history = train_head(x_tr, y_train_views, x_va, data["val"][1], tcfg, n_classes, arch, seed,
                                   log_path=out_dir / "history.csv", verbose=0)
        # Put the trained head on its frozen backbones: an ordinary end-to-end model for every other script.
        full, backbones = build_model(arch, n_classes, dcfg["img_size"], weights, tcfg["resnet_variant"], tcfg["effnet_variant"],
                                      tcfg["dropout_1"], tcfg["dense_units"], tcfg["dropout_2"], tcfg["l2"], effnet_weights_file=effnet_file)
        for name in ("fc", "logits"):
            full.get_layer(name).set_weights(head.get_layer(name).get_weights())
        val_paths, y_val, _ = data["val"]
        probs_full = full.predict(tf.data.Dataset.from_tensor_slices((val_paths, y_val))
                                  .map(_loader(dcfg["img_size"], n_classes)).batch(32), verbose=0)
        probs_head = head.predict(x_va, verbose=0)
        agreement = float(np.mean(probs_full.argmax(1) == probs_head.argmax(1)))
        max_diff = float(np.abs(probs_full - probs_head).max())
        full.save(out_dir / "model.keras")
        metrics = compute_metrics(y_val, probs_full, class_names)
        epochs = len(history["loss"])
        meta = {
            "model_version": f"{arch}-cached-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M')}",
            "arch": arch, "backbones": [b.name for b in backbones], "class_names": class_names,
            "img_size": dcfg["img_size"], "processed_size": dcfg["processed_size"], "crop_faces": dcfg["crop_faces"],
            "face_margin": dcfg["face_margin"], "input": "RGB float32 in [0, 255], shape (N, img_size, img_size, 3)",
            "weights_init": "imagenet" + (" (EfficientNetB0: Noisy Student ImageNet weights, local file)" if effnet_file else ""),
            "training_method": f"train_cached.py: frozen backbones, cached features ({n_views} views per training image), "
                               "head trained with Adam, label smoothing and class weights; no fine-tuning",
            "params": {"total": int(full.count_params()), "trainable_head": int(head.count_params())},
            "train_counts": dict(zip(class_names, np.bincount(data["train"][1], minlength=n_classes).tolist())),
            "val_counts": dict(zip(class_names, np.bincount(y_val, minlength=n_classes).tolist())),
            "val_metrics": {"accuracy": metrics["accuracy"], "macro_f1": metrics["macro"]["f1"]},
            "head_vs_full_model_check": {"top1_agreement": agreement, "max_probability_difference": max_diff},
            "epochs_run": {"head": epochs, "finetune": 0},
            "training_seconds": round(time.time() - t0 + feature_seconds, 1),
            "versions": {"tensorflow": tf.__version__, "keras": keras.__version__, "python": platform.python_version()},
            "config": {key: cfg[key] for key in ("data", "augmentation", "training")},
            "created_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        }
        save_json(meta, out_dir / "model_meta.json")
        with open(out_dir / "history.csv", newline="", encoding="utf-8") as fh:
            rows = list(csv.DictReader(fh))
        plot_history({k: [float(r[k]) for r in rows] for k in rows[0] if k != "epoch"}, out_dir / "training_curves.png")
        print(f"\n[{arch}] {epochs} epochs; head vs full model: top-1 agreement {agreement:.1%}, max |dp| {max_diff:.2e}")
        print(format_summary(metrics))
        print(f"Saved {out_dir / 'model.keras'}")


if __name__ == "__main__":
    main()
