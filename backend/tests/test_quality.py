"""Unit tests for the photo-quality gate (CD-5 cases F-17 to F-19)."""
import cv2
import numpy as np

from glowrithm_ml.quality import assess_quality

SHAPE = (1000, 800)          # original photo height, width
BOX = (200, 250, 400, 400)   # face box x, y, w, h -> face width is 50% of the photo


def textured(scale=1.0, seed=0):
    rng = np.random.default_rng(seed)
    return np.clip(rng.integers(60, 200, (384, 384, 3)) * scale, 0, 255).astype(np.uint8)


def status(report, name):
    return next(check["status"] for check in report["checks"] if check["name"] == name)


def test_good_photo_passes():
    report = assess_quality(textured(), SHAPE, BOX)
    assert report["passed"] and not report["issues"]


def test_dark_photo_fails():
    report = assess_quality(textured(0.25), SHAPE, BOX)
    assert not report["passed"] and status(report, "brightness") == "fail"


def test_blurry_photo_fails():
    report = assess_quality(cv2.GaussianBlur(textured(), (0, 0), 8), SHAPE, BOX)
    assert not report["passed"] and status(report, "sharpness") == "fail"


def test_flash_glare_fails():
    image = textured()
    image[:120] = 255  # about 31% clipped pixels, as with a flash reflection
    report = assess_quality(image, SHAPE, BOX)
    assert not report["passed"] and status(report, "glare") == "fail"


def test_small_face_fails():
    report = assess_quality(textured(), SHAPE, (370, 450, 90, 90))
    assert not report["passed"] and status(report, "face_size") == "fail"


def test_missing_face_warns_unless_required():
    assert assess_quality(textured(), SHAPE, None)["passed"]
    assert not assess_quality(textured(), SHAPE, None, require_face=True)["passed"]
