"""Image preprocessing shared by training (prepare_dataset.py) and serving (backend API).

Using one implementation in both places prevents training/serving skew:

    decode (EXIF-aware) -> detect the largest frontal face (Haar cascade, Viola-Jones)
    -> square crop around the face with a margin (fallback: centre square crop)
    -> resize to `processed_size` (saved crop / image shown in the app)
    -> resize to the model resolution `img_size` (bilinear, antialiased) -> float32 RGB in [0, 255]

The model itself contains the backbone-specific normalisation layers, so callers always feed
plain RGB values in [0, 255].
"""
from __future__ import annotations

import io
from dataclasses import dataclass

import cv2
import numpy as np
from PIL import Image, ImageOps

# CD-2: input photos are JPEG/PNG. MPO is the multi-picture JPEG some phone cameras write.
ALLOWED_FORMATS = frozenset({"JPEG", "PNG", "MPO"})

_FACE_CASCADE: cv2.CascadeClassifier | None = None


class InvalidImageError(ValueError):
    """Raised when uploaded bytes are not a readable JPEG/PNG image."""


@dataclass
class PreparedImage:
    display: np.ndarray       # uint8 (processed_size, processed_size, 3) square crop
    model_input: np.ndarray   # float32 (img_size, img_size, 3) in [0, 255]
    face_found: bool
    face_box: tuple[int, int, int, int] | None = None  # (x, y, w, h) in the original photo


def _cascade() -> cv2.CascadeClassifier:
    global _FACE_CASCADE
    if _FACE_CASCADE is None:
        path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        cascade = cv2.CascadeClassifier(path)
        if cascade.empty():
            raise RuntimeError(f"Could not load the Haar cascade from {path}")
        _FACE_CASCADE = cascade
    return _FACE_CASCADE


def decode_image_bytes(data: bytes, allowed_formats: frozenset[str] | None = ALLOWED_FORMATS) -> np.ndarray:
    """Decode bytes to an RGB uint8 array, applying the EXIF orientation written by phone cameras."""
    try:
        img = Image.open(io.BytesIO(data))
        fmt = img.format
        img.load()
    except Exception as exc:  # PIL raises many different exception types
        raise InvalidImageError("The file is not a readable image.") from exc
    if allowed_formats is not None and fmt not in allowed_formats:
        raise InvalidImageError(f"Unsupported image format '{fmt}'. Upload a JPEG or PNG photo.")
    img = ImageOps.exif_transpose(img)
    return np.asarray(img.convert("RGB"))


def load_image_file(path) -> np.ndarray:
    with open(path, "rb") as fh:
        return decode_image_bytes(fh.read(), allowed_formats=None)


def detect_face(rgb: np.ndarray, min_size_ratio: float = 0.15) -> tuple[int, int, int, int] | None:
    """Return the largest frontal face box (x, y, w, h) in original pixel units, or None."""
    gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
    h, w = gray.shape
    scale = 1.0
    if max(h, w) > 800:  # detection on a downscaled copy is faster and just as reliable
        scale = 800.0 / max(h, w)
        gray = cv2.resize(gray, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_AREA)
    gray = cv2.equalizeHist(gray)
    min_side = max(24, int(min(gray.shape) * min_size_ratio))
    faces = _cascade().detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(min_side, min_side))
    if len(faces) == 0:
        return None
    x, y, fw, fh = max(faces, key=lambda box: box[2] * box[3])
    return tuple(int(round(v / scale)) for v in (x, y, fw, fh))


def square_crop(rgb: np.ndarray, box: tuple[int, int, int, int] | None = None, margin: float = 0.30) -> np.ndarray:
    """Square crop centred on `box` (side = (1 + margin) * max(w, h)); centre crop when box is None.
    Regions outside the image are filled by edge replication so the crop is always square."""
    h, w = rgb.shape[:2]
    if box is None:
        side, cx, cy = min(h, w), w / 2.0, h / 2.0
    else:
        x, y, bw, bh = box
        side, cx, cy = max(bw, bh) * (1.0 + margin), x + bw / 2.0, y + bh / 2.0
    side = max(1, int(round(side)))
    x0, y0 = int(round(cx - side / 2.0)), int(round(cy - side / 2.0))
    pad = max(0, -x0, -y0, x0 + side - w, y0 + side - h)
    if pad:
        rgb = cv2.copyMakeBorder(rgb, pad, pad, pad, pad, cv2.BORDER_REPLICATE)
        x0, y0 = x0 + pad, y0 + pad
    return np.ascontiguousarray(rgb[y0:y0 + side, x0:x0 + side])


def prepare_face(rgb: np.ndarray, crop_faces: bool = True, margin: float = 0.30) -> tuple[np.ndarray, bool]:
    box = detect_face(rgb) if crop_faces else None
    return square_crop(rgb, box, margin), box is not None


def resize_square(rgb: np.ndarray, size: int) -> np.ndarray:
    interpolation = cv2.INTER_AREA if rgb.shape[0] > size else cv2.INTER_CUBIC
    return cv2.resize(rgb, (size, size), interpolation=interpolation)


def to_model_input(rgb: np.ndarray, img_size: int) -> np.ndarray:
    """Exactly the resize used by the tf.data pipeline (bilinear + antialias, float32 0..255)."""
    import tensorflow as tf  # local import: dataset preparation does not need TensorFlow

    tensor = tf.convert_to_tensor(rgb, dtype=tf.float32)
    return tf.image.resize(tensor, (img_size, img_size), method="bilinear", antialias=True).numpy()


def preprocess_for_model(rgb: np.ndarray, *, crop_faces: bool, margin: float,
                         processed_size: int, img_size: int) -> PreparedImage:
    box = detect_face(rgb) if crop_faces else None
    display = resize_square(square_crop(rgb, box, margin), processed_size)
    return PreparedImage(display=display, model_input=to_model_input(display, img_size),
                         face_found=box is not None, face_box=box)
