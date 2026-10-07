#!/usr/bin/env python3
"""Test fixtures for e2e_webapp.mjs, made from scikit-image's public-domain "astronaut" portrait (NASA).

    python make_fixtures.py fixtures

face_sharp.jpg  1536 px sharpened portrait that passes the quality gate (gallery upload test)
dark.jpg        the same photo at 18 % brightness, which the quality gate must reject
face.y4m        1280 x 720 video for Chrome's fake camera; the portrait sits in the centre, where a phone-shaped
                preview crops it, so the captured photo passes the face-size check
"""
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter
from skimage import data

out = Path(sys.argv[1] if len(sys.argv) > 1 else "fixtures")
out.mkdir(parents=True, exist_ok=True)
portrait = Image.fromarray(data.astronaut()).convert("RGB")
sharp = portrait.resize((1536, 1536), Image.LANCZOS).filter(ImageFilter.UnsharpMask(radius=3, percent=220, threshold=2))
sharp.save(out / "face_sharp.jpg", quality=93)
Image.fromarray((np.asarray(sharp).astype(float) * 0.18).astype("uint8")).save(out / "dark.jpg", quality=92)

frame = Image.new("RGB", (1280, 720), (120, 125, 122))
frame.paste(sharp.crop((330, 60, 1050, 780)).resize((720, 720), Image.LANCZOS), (280, 0))
y, cb, cr = [np.asarray(channel) for channel in frame.convert("YCbCr").split()]
half = lambda c: c.reshape(360, 2, 640, 2).mean(axis=(1, 3)).astype(np.uint8)  # noqa: E731  4:2:0 chroma
with open(out / "face.y4m", "wb") as fh:
    fh.write(b"YUV4MPEG2 W1280 H720 F30:1 Ip A1:1 C420jpeg\n")
    for _ in range(30):
        fh.write(b"FRAME\n" + y.tobytes() + half(cb).tobytes() + half(cr).tobytes())
print(f"Fixtures written to {out}")
