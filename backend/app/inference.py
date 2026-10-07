"""Model loading and inference (prediction + Grad-CAM). Photos are processed in memory only."""
from __future__ import annotations

import base64
import io
import json
import logging
import threading
import time

import numpy as np
from PIL import Image

from glowrithm_ml.gradcam import GradCAM, colorize
from glowrithm_ml.preprocessing import decode_image_bytes, preprocess_for_model, resize_square
from glowrithm_ml.quality import assess_quality

from .config import Settings

logger = logging.getLogger("glowrithm.inference")

DEFAULT_META = {"class_names": ["dry", "normal", "oily"], "img_size": 224, "processed_size": 384,
                "crop_faces": True, "face_margin": 0.30, "model_version": "unknown"}


def _jpeg_b64(rgb: np.ndarray, quality: int = 88) -> str:
    buffer = io.BytesIO()
    Image.fromarray(rgb).save(buffer, format="JPEG", quality=quality)
    return base64.b64encode(buffer.getvalue()).decode("ascii")


class PhotoQualityError(ValueError):
    """Raised by the quality gate; `report` holds every check and the advice for the user."""

    def __init__(self, report: dict):
        super().__init__(" ".join(report["issues"]))
        self.report = report


class InferenceEngine:
    """Loads the Keras model once; a lock serialises inference on the shared model object."""

    def __init__(self, model, meta: dict, demo: bool = False):
        self.meta = {**DEFAULT_META, **meta}
        self.class_names = list(self.meta["class_names"])
        self.demo = demo
        self._explainer = GradCAM(model)
        self._lock = threading.Lock()
        size = int(self.meta["img_size"])
        self._explainer.explain(np.zeros((1, size, size, 3), np.float32))  # warm-up builds the TF graph

    @property
    def model_version(self) -> str:
        return str(self.meta.get("model_version", "unknown"))

    @classmethod
    def from_settings(cls, settings: Settings) -> "InferenceEngine":
        if settings.demo_mode:
            from glowrithm_ml.model import build_demo_model

            meta = {**DEFAULT_META, "model_version": "demo-untrained"}
            return cls(build_demo_model(len(meta["class_names"]), meta["img_size"]), meta, demo=True)
        if not settings.model_path.exists():
            raise FileNotFoundError(
                f"{settings.model_path} not found. Train the model (ml/scripts/train.py), copy model.keras and "
                "model_meta.json to backend/models/, or set GLOWRITHM_DEMO_MODE=1 for app development.")
        import keras

        model = keras.saving.load_model(settings.model_path, compile=False)
        meta_path = settings.resolved_meta_path
        meta = json.loads(meta_path.read_text(encoding="utf-8")) if meta_path.exists() else {}
        if not meta:
            logger.warning("model_meta.json not found next to the model; using defaults %s", DEFAULT_META)
        trained_with = meta.get("versions", {}).get("keras")
        if trained_with and trained_with.split(".")[:2] != keras.__version__.split(".")[:2]:
            logger.warning("Model trained with Keras %s, server runs %s", trained_with, keras.__version__)
        return cls(model, meta)

    def analyze(self, image_bytes: bytes, display_size: int = 384, quality_mode: str = "reject",
                require_face: bool = False) -> dict:
        started = time.perf_counter()
        rgb = decode_image_bytes(image_bytes)  # raises InvalidImageError for non JPEG/PNG data
        prepared = preprocess_for_model(rgb, crop_faces=bool(self.meta["crop_faces"]),
                                        margin=float(self.meta["face_margin"]),
                                        processed_size=int(self.meta["processed_size"]),
                                        img_size=int(self.meta["img_size"]))
        quality = None
        if quality_mode != "off":  # runs before the model, so a rejected photo costs no inference
            quality = {**assess_quality(prepared.display, rgb.shape[:2], prepared.face_box, require_face),
                       "mode": quality_mode}
            if quality_mode == "reject" and not quality["passed"]:
                raise PhotoQualityError(quality)
        preprocessed = time.perf_counter()
        with self._lock:
            result = self._explainer.explain(prepared.model_input[None])
        explained = time.perf_counter()

        probs, index = result["probabilities"], result["class_index"]
        face = prepared.display
        if face.shape[0] != display_size:
            face = resize_square(face, display_size)
        output = {
            "skin_type": self.class_names[index],
            "confidence": float(probs[index]),
            "probabilities": {name: round(float(p), 4) for name, p in zip(self.class_names, probs)},
            "face_detected": prepared.face_found,
            "face_image": _jpeg_b64(face),
            "heatmap_image": _jpeg_b64(colorize(result["cam"], size=display_size)),
            "quality": quality,
        }
        output["timings_ms"] = {
            "preprocess_and_quality": round((preprocessed - started) * 1000, 1),
            "model_and_gradcam": round((explained - preprocessed) * 1000, 1),
            "encode": round((time.perf_counter() - explained) * 1000, 1),
        }
        return output
