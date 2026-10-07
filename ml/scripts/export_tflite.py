#!/usr/bin/env python3
"""Convert the Keras model to TensorFlow Lite (optional on-device inference; Grad-CAM still needs the server).

    python scripts/export_tflite.py --model artifacts/ensemble/model.keras --quantize float16

--quantize: none (float32) | float16 (about half the size) | dynamic (int8 weights, about a quarter).
Checks top-1 agreement between the Keras and TFLite models on random inputs and writes
model_<quantize>.tflite + labels.txt next to the Keras model.
"""
from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import keras  # noqa: E402
import tensorflow as tf  # noqa: E402

from glowrithm_ml.config import load_json, meta_path_for  # noqa: E402


def convert(model: keras.Model, work_dir: Path, quantize: str) -> bytes:
    saved = work_dir / "saved_model_tmp"
    shutil.rmtree(saved, ignore_errors=True)
    model.export(str(saved))  # Keras 3: TF SavedModel with a serving signature
    converter = tf.lite.TFLiteConverter.from_saved_model(str(saved))
    if quantize in ("float16", "dynamic"):
        converter.optimizations = [tf.lite.Optimize.DEFAULT]
    if quantize == "float16":
        converter.target_spec.supported_types = [tf.float16]
    data = converter.convert()
    shutil.rmtree(saved, ignore_errors=True)
    return data


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--model", required=True)
    parser.add_argument("--quantize", default="float16", choices=["none", "float16", "dynamic"])
    parser.add_argument("--check-samples", type=int, default=8)
    args = parser.parse_args()

    meta = load_json(meta_path_for(args.model))
    model = keras.saving.load_model(args.model, compile=False)
    out_dir = Path(args.model).parent
    target = out_dir / f"model_{args.quantize}.tflite"
    target.write_bytes(convert(model, out_dir, args.quantize))
    (out_dir / "labels.txt").write_text("\n".join(meta["class_names"]) + "\n", encoding="utf-8")

    interpreter = tf.lite.Interpreter(model_path=str(target))
    interpreter.allocate_tensors()
    inp, out = interpreter.get_input_details()[0], interpreter.get_output_details()[0]
    rng = np.random.default_rng(0)
    agree, max_diff = 0, 0.0
    for _ in range(args.check_samples):
        x = rng.uniform(0, 255, (1, meta["img_size"], meta["img_size"], 3)).astype(np.float32)
        interpreter.set_tensor(inp["index"], x)
        interpreter.invoke()
        lite = interpreter.get_tensor(out["index"])[0]
        ref = np.asarray(model(x, training=False))[0]
        agree += int(lite.argmax() == ref.argmax())
        max_diff = max(max_diff, float(np.abs(lite - ref).max()))
    keras_mb = Path(args.model).stat().st_size / 2**20
    print(f"Saved {target} ({target.stat().st_size / 2**20:.1f} MB; Keras model {keras_mb:.1f} MB)")
    print(f"Input {inp['shape']} {inp['dtype'].__name__} in [0, 255]; output order {meta['class_names']}")
    print(f"Top-1 agreement with Keras: {agree}/{args.check_samples}, max |prob diff| = {max_diff:.4f}")


if __name__ == "__main__":
    main()
