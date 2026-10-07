"""Photo-quality gate: rejects photos the model cannot judge reliably (CD-2: kondisi pengambilan citra).

Measured on the square face crop (processed_size px, e.g. 384) so the values do not depend on the phone's
camera resolution:
  brightness  mean luma Y (0-255)                    fail < 60 or > 215     warn < 85 or > 190
  glare       share of clipped pixels (Y >= 250)     fail > 0.15            warn > 0.06   (flash, direct lamp)
  sharpness   variance of the Laplacian of Y         fail < 25              warn < 60     (motion or focus blur)
  face_size   face-box width / photo width           fail < 0.18            warn < 0.28   (face too far away)
  face        frontal face detected                  warn when missing (fail if require_face)
The defaults are starting points: calibrate them on your own data with scripts/quality_report.py.
"""
from __future__ import annotations

from dataclasses import dataclass

import cv2
import numpy as np

MESSAGES = {
    "brightness_low": "The photo is too dark. Face a window or another soft, even light.",
    "brightness_high": "The photo is too bright. Move out of direct light.",
    "glare": "Strong reflections were found. Turn off the flash and avoid lamps pointed at your face; "
             "reflections look like oily skin to the model.",
    "sharpness": "The photo is blurry. Hold the phone still and let the camera focus.",
    "face_size": "Your face is too small in the photo. Move closer so that it fills the oval.",
    "face": "No face was found. Face the camera directly with your whole face visible.",
}


@dataclass(frozen=True)
class QualityThresholds:
    brightness_fail: tuple[float, float] = (60.0, 215.0)
    brightness_warn: tuple[float, float] = (85.0, 190.0)
    glare_fail: float = 0.15
    glare_warn: float = 0.06
    sharpness_fail: float = 25.0
    sharpness_warn: float = 60.0
    face_fail: float = 0.18
    face_warn: float = 0.28


def measure(face_crop: np.ndarray) -> dict[str, float]:
    """Brightness (mean luma), glare (share of clipped pixels) and sharpness (Laplacian variance)."""
    luma = cv2.cvtColor(face_crop, cv2.COLOR_RGB2GRAY).astype(np.float32)
    return {
        "brightness": float(luma.mean()),
        "glare": float((luma >= 250).mean()),
        "sharpness": float(cv2.Laplacian(luma, cv2.CV_32F).var()),
    }


def _grade(value: float, fail: float, warn: float, higher_is_worse: bool) -> str:
    if higher_is_worse:
        return "fail" if value > fail else "warn" if value > warn else "ok"
    return "fail" if value < fail else "warn" if value < warn else "ok"


def assess_quality(face_crop: np.ndarray, image_shape: tuple[int, ...], face_box, require_face: bool = False,
                   thresholds: QualityThresholds | None = None) -> dict:
    """Return {"passed", "checks": [{name, value, status, message}], "issues": [advice for the user]}."""
    t = thresholds or QualityThresholds()
    m = measure(face_crop)
    checks: list[dict] = []

    def add(name: str, value: float | None, status: str, key: str) -> None:
        checks.append({"name": name, "value": None if value is None else round(value, 4), "status": status,
                       "message": MESSAGES[key] if status != "ok" else ""})

    b = m["brightness"]
    if b < t.brightness_warn[0]:
        add("brightness", b, "fail" if b < t.brightness_fail[0] else "warn", "brightness_low")
    else:
        status = "fail" if b > t.brightness_fail[1] else "warn" if b > t.brightness_warn[1] else "ok"
        add("brightness", b, status, "brightness_high")
    add("glare", m["glare"], _grade(m["glare"], t.glare_fail, t.glare_warn, True), "glare")
    add("sharpness", m["sharpness"], _grade(m["sharpness"], t.sharpness_fail, t.sharpness_warn, False), "sharpness")
    if face_box is None:
        add("face", None, "fail" if require_face else "warn", "face")
    else:
        ratio = face_box[2] / float(image_shape[1])
        add("face_size", ratio, _grade(ratio, t.face_fail, t.face_warn, False), "face_size")
    return {"passed": all(c["status"] != "fail" for c in checks), "checks": checks,
            "issues": [c["message"] for c in checks if c["status"] != "ok"]}
