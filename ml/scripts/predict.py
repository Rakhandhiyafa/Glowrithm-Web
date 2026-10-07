#!/usr/bin/env python3
"""Classify one photo and save its Grad-CAM overlay (quick manual check).

    python scripts/predict.py --model artifacts/ensemble/model.keras --image face.jpg --out face_gradcam.jpg
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import keras  # noqa: E402

from glowrithm_ml.config import load_json, meta_path_for  # noqa: E402
from glowrithm_ml.gradcam import GradCAM, overlay  # noqa: E402
from glowrithm_ml.preprocessing import load_image_file, preprocess_for_model  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--model", required=True)
    parser.add_argument("--image", required=True)
    parser.add_argument("--out", default="gradcam_overlay.jpg")
    args = parser.parse_args()

    meta = load_json(meta_path_for(args.model))
    prepared = preprocess_for_model(load_image_file(args.image), crop_faces=meta["crop_faces"],
                                    margin=meta["face_margin"], processed_size=meta["processed_size"],
                                    img_size=meta["img_size"])
    result = GradCAM(keras.saving.load_model(args.model, compile=False)).explain(prepared.model_input[None])
    probs = result["probabilities"]
    for name, p in sorted(zip(meta["class_names"], probs), key=lambda t: -t[1]):
        print(f"{name:<7} {p:6.1%}")
    print(f"Face detected: {prepared.face_found}")
    Image.fromarray(np.hstack([prepared.display, overlay(prepared.display, result["cam"])])).save(args.out, quality=92)
    print(f"Saved {args.out}")


if __name__ == "__main__":
    main()
