#!/usr/bin/env python3
"""Computational-efficiency benchmark for CD-5: model size, parameters and latency.

    python scripts/benchmark.py --model artifacts/ensemble/model.keras --image sample.jpg \
        [--tflite artifacts/ensemble/model_float16.tflite] --runs 30

Measures (single image, after warm-up): preprocessing (face detection + crop), Keras prediction,
Grad-CAM (forward + backward pass) and, optionally, TFLite inference. Writes benchmark.json.
"""
from __future__ import annotations

import argparse
import platform
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import keras  # noqa: E402
import tensorflow as tf  # noqa: E402

from glowrithm_ml.config import load_json, meta_path_for, save_json  # noqa: E402
from glowrithm_ml.gradcam import GradCAM  # noqa: E402
from glowrithm_ml.model import count_params  # noqa: E402
from glowrithm_ml.preprocessing import load_image_file, preprocess_for_model  # noqa: E402


def timed(fn, runs: int, warmup: int = 3) -> dict:
    for _ in range(warmup):
        fn()
    samples = []
    for _ in range(runs):
        start = time.perf_counter()
        fn()
        samples.append((time.perf_counter() - start) * 1000)
    arr = np.array(samples)
    return {"mean_ms": round(float(arr.mean()), 2), "p50_ms": round(float(np.percentile(arr, 50)), 2),
            "p95_ms": round(float(np.percentile(arr, 95)), 2), "runs": runs}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--model", required=True)
    parser.add_argument("--image", help="a face photo; random pixels are used when omitted")
    parser.add_argument("--tflite")
    parser.add_argument("--runs", type=int, default=30)
    args = parser.parse_args()

    meta = load_json(meta_path_for(args.model))
    model = keras.saving.load_model(args.model, compile=False)
    trainable, frozen = count_params(model)
    report = {"model": str(args.model), "model_version": meta.get("model_version"),
              "model_size_mb": round(Path(args.model).stat().st_size / 2**20, 2),
              "parameters": trainable + frozen, "device": platform.processor() or platform.machine(),
              "tensorflow": tf.__version__, "gpu": bool(tf.config.list_physical_devices("GPU"))}

    if args.image:
        rgb = load_image_file(args.image)
    else:
        rgb = np.random.default_rng(0).integers(0, 255, (960, 720, 3), dtype=np.uint8)
    prep = lambda: preprocess_for_model(rgb, crop_faces=meta["crop_faces"], margin=meta["face_margin"],  # noqa: E731
                                        processed_size=meta["processed_size"], img_size=meta["img_size"])
    report["preprocessing"] = timed(prep, args.runs)
    batch = prep().model_input[None]
    report["keras_predict"] = timed(lambda: model(batch, training=False), args.runs)
    explainer = GradCAM(model)
    report["gradcam_with_prediction"] = timed(lambda: explainer.explain(batch), args.runs)

    if args.tflite:
        interpreter = tf.lite.Interpreter(model_path=args.tflite)
        interpreter.allocate_tensors()
        inp, out = interpreter.get_input_details()[0], interpreter.get_output_details()[0]

        def run_lite():
            interpreter.set_tensor(inp["index"], batch.astype(np.float32))
            interpreter.invoke()
            return interpreter.get_tensor(out["index"])

        report["tflite_size_mb"] = round(Path(args.tflite).stat().st_size / 2**20, 2)
        report["tflite_invoke"] = timed(run_lite, args.runs)

    out_path = Path(args.model).parent / "reports" / "benchmark.json"
    save_json(report, out_path)
    for key, value in report.items():
        print(f"{key:<26}{value}")
    print(f"Saved {out_path}")


if __name__ == "__main__":
    main()
