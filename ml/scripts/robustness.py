#!/usr/bin/env python3
"""Robustness test: accuracy under photo conditions the app meets in the field (CD-2 / CD-3 stability).

    python scripts/robustness.py --model artifacts/ensemble/model.keras --split test

Each perturbation is applied to the processed face crops before resizing to the model input.
Writes <model folder>/reports/robustness/robustness.csv, robustness.json and robustness.png.
"""
from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import keras  # noqa: E402
import tensorflow as tf  # noqa: E402

from glowrithm_ml.config import load_config, load_json, meta_path_for, save_json  # noqa: E402
from glowrithm_ml.data import load_split  # noqa: E402
from glowrithm_ml.metrics import compute_metrics  # noqa: E402

RNG = np.random.default_rng(42)


def _clip(x: np.ndarray) -> np.ndarray:
    return np.clip(x, 0, 255).astype(np.uint8)


def _jpeg(quality: int):
    def apply(im):
        ok, buf = cv2.imencode(".jpg", cv2.cvtColor(im, cv2.COLOR_RGB2BGR), [cv2.IMWRITE_JPEG_QUALITY, quality])
        return cv2.cvtColor(cv2.imdecode(buf, cv2.IMREAD_COLOR), cv2.COLOR_BGR2RGB)
    return apply


def _rotate(degrees: float):
    def apply(im):
        h, w = im.shape[:2]
        matrix = cv2.getRotationMatrix2D((w / 2, h / 2), degrees, 1.0)
        return cv2.warpAffine(im, matrix, (w, h), borderMode=cv2.BORDER_REFLECT_101)
    return apply


def _warm(im):
    x = im.astype(np.float32)
    x[..., 0] *= 1.12  # more red
    x[..., 2] *= 0.85  # less blue: indoor tungsten light
    return _clip(x)


PERTURBATIONS = {
    "clean": lambda im: im,
    "dark (-40% brightness)": lambda im: _clip(im.astype(np.float32) * 0.6),
    "bright (+40% brightness)": lambda im: _clip(im.astype(np.float32) * 1.4),
    "low contrast (x0.6)": lambda im: _clip((im.astype(np.float32) - im.mean()) * 0.6 + im.mean()),
    "warm indoor light": _warm,
    "gaussian blur (7x7)": lambda im: cv2.GaussianBlur(im, (7, 7), 0),
    "sensor noise (sigma 15)": lambda im: _clip(im.astype(np.float32) + RNG.normal(0, 15, im.shape)),
    "jpeg quality 30": _jpeg(30),
    "head tilt 15 deg": _rotate(15),
}


def predict(model, images: list[np.ndarray], img_size: int, batch: int = 32) -> np.ndarray:
    out = []
    for i in range(0, len(images), batch):
        x = tf.image.resize(tf.convert_to_tensor(np.stack(images[i:i + batch]), tf.float32),
                            (img_size, img_size), method="bilinear", antialias=True)
        out.append(np.asarray(model.predict_on_batch(x)))
    return np.concatenate(out)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--model", required=True)
    parser.add_argument("--config", default="config.yaml")
    parser.add_argument("--split", default="test")
    args = parser.parse_args()

    cfg = load_config(args.config)
    meta = load_json(meta_path_for(args.model))
    class_names = meta["class_names"]
    out_dir = Path(args.model).parent / "reports" / "robustness"
    out_dir.mkdir(parents=True, exist_ok=True)

    paths, labels = load_split(cfg["paths"]["manifest"], args.split, class_names)
    images = [np.asarray(Image.open(p).convert("RGB")) for p in paths]
    model = keras.saving.load_model(args.model, compile=False)

    results, clean_acc = [], None
    for name, fn in PERTURBATIONS.items():
        probs = predict(model, [fn(im) for im in images], meta["img_size"])
        m = compute_metrics(labels, probs, class_names)
        clean_acc = m["accuracy"] if name == "clean" else clean_acc
        results.append({"condition": name, "accuracy": round(m["accuracy"], 4), "macro_f1": round(m["macro"]["f1"], 4),
                        "accuracy_drop_pp": round(100 * (clean_acc - m["accuracy"]), 2)})
        print(f"{name:<26} accuracy {m['accuracy']:.4f}  macro-F1 {m['macro']['f1']:.4f}")

    with open(out_dir / "robustness.csv", "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(results[0]))
        writer.writeheader()
        writer.writerows(results)
    save_json({"split": args.split, "n_images": len(paths), "results": results}, out_dir / "robustness.json")

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(8, 4), dpi=150)
    ax.barh([r["condition"] for r in results][::-1], [100 * r["accuracy"] for r in results][::-1], color="#0E5C58")
    ax.axvline(100 * cfg["evaluation"]["target_accuracy"], color="#E0522B", linestyle="--", label="CD-3 target")
    ax.set(xlabel="Accuracy (%)", xlim=(0, 100), title=f"Robustness on the {args.split} split (n = {len(paths)})")
    ax.legend(loc="lower right")
    fig.tight_layout()
    fig.savefig(out_dir / "robustness.png")
    print(f"Saved {out_dir}")


if __name__ == "__main__":
    main()
