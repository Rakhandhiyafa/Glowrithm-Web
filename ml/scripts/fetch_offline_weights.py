#!/usr/bin/env python3
"""Prepare ImageNet backbone weights on networks where Keras cannot reach storage.googleapis.com.

Only needed in restricted environments (it was used for the initial CPU test of the Kaggle dataset).
On Colab or any normal network, `weights: imagenet` downloads the standard Keras weights by itself.

1. ResNet50V2: downloads the official file from the keras-team/keras-applications GitHub release into the Keras
   cache (~/.keras/models). It is byte-identical to the file Keras expects (MD5 checked against Keras's own
   table), so `keras.applications.ResNet50V2(weights="imagenet")` then works offline.
2. EfficientNetB0: downloads the Noisy Student ImageNet weights released by the qubvel/efficientnet project
   (same layer names as keras.applications.EfficientNetB0), ports them by layer name, sets the input
   normalisation to the ImageNet mean/std, verifies them by classifying two sample photos with the ImageNet head,
   and saves `efficientnetb0_noisy-student_notop.weights.h5` for `training.effnet_weights_file` in config.yaml.

    python scripts/fetch_offline_weights.py --out ~/.keras/models
"""
from __future__ import annotations

import argparse
import hashlib
import sys
import urllib.request
from pathlib import Path

import h5py
import numpy as np

RESNET = ("https://github.com/keras-team/keras-applications/releases/download/resnet/"
          "resnet50v2_weights_tf_dim_ordering_tf_kernels_notop.h5", "fac2f116257151a9d068a22e544a4917")
EFFNET = {
    "notop": ("https://github.com/qubvel/efficientnet/releases/download/v0.0.1/efficientnet-b0_noisy-student_notop.h5",
              "a5b48ae7547fc990c7e4f3951230290d"),
    "top": ("https://github.com/qubvel/efficientnet/releases/download/v0.0.1/efficientnet-b0_noisy-student.h5",
            "5e376ca93bc6ba60f5245d13d44e4323"),
}
IMAGENET_MEAN = [0.485, 0.456, 0.406]
IMAGENET_STD = [0.229, 0.224, 0.225]
# Sanity check: scikit-image sample photos and the ImageNet classes they must fall into.
CHECKS = {"chelsea": ({281, 282, 283, 284, 285, 287}, "cat"), "coffee": ({504, 967, 968}, "cup / espresso")}


def md5(path: Path) -> str:
    digest = hashlib.md5()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def fetch(url: str, expected_md5: str, target: Path) -> Path:
    if target.exists() and md5(target) == expected_md5:
        print(f"ok (cached)  {target.name}")
        return target
    print(f"downloading {url}")
    tmp = target.with_suffix(".part")
    urllib.request.urlretrieve(url, tmp)
    got = md5(tmp)
    if got != expected_md5:
        tmp.unlink(missing_ok=True)
        sys.exit(f"MD5 mismatch for {target.name}: {got} != {expected_md5}")
    tmp.rename(target)
    print(f"ok (md5 {got})  {target.name}")
    return target


def legacy_h5_weights(path: Path) -> dict[str, list[np.ndarray]]:
    """Read a Keras-2 HDF5 weights file into {layer name: [arrays in saved order]}."""
    out = {}
    with h5py.File(path, "r") as f:
        group = f["model_weights"] if "model_weights" in f else f
        for name in group.attrs["layer_names"]:
            name = name.decode() if isinstance(name, bytes) else name
            weight_names = group[name].attrs["weight_names"]
            out[name] = [np.asarray(group[name][w.decode() if isinstance(w, bytes) else w]) for w in weight_names]
    return out


def port_efficientnet(model, saved: dict[str, list[np.ndarray]], rename: dict[str, str] | None = None) -> None:
    """Copy weights by layer name and shape; set the Normalization layer to ImageNet mean/std."""
    import keras

    rename = rename or {}
    loaded, missing = 0, []
    for layer in model.layers:
        if isinstance(layer, keras.layers.Normalization):
            mean = np.asarray(IMAGENET_MEAN, dtype=np.float32)
            var = np.square(np.asarray(IMAGENET_STD, dtype=np.float32))
            layer.set_weights([mean, var, np.asarray(0, dtype=layer.weights[2].dtype)])
            layer.finalize_state()
            continue
        if not layer.weights:
            continue
        arrays = saved.get(rename.get(layer.name, layer.name))
        if arrays is None or [a.shape for a in arrays] != [tuple(w.shape) for w in layer.weights]:
            missing.append(layer.name)
            continue
        layer.set_weights(arrays)
        loaded += 1
    if missing:
        sys.exit(f"Could not port {len(missing)} layers, e.g. {missing[:5]}")
    print(f"ported {loaded} layers")


def verify(model) -> None:
    from PIL import Image
    from skimage import data

    for name, (classes, label) in CHECKS.items():
        img = Image.fromarray(getattr(data, name)()).convert("RGB")
        side = min(img.size)
        left, top = (img.width - side) // 2, (img.height - side) // 2
        x = np.asarray(img.crop((left, top, left + side, top + side)).resize((224, 224), Image.BICUBIC), np.float32)
        probs = np.asarray(model.predict(x[None], verbose=0))[0]
        top5 = np.argsort(-probs)[:5]
        status = "OK" if int(top5[0]) in classes else "FAILED"
        print(f"{name}: top-5 ImageNet classes {top5.tolist()} (p={probs[top5[0]]:.2f}) expected {label}: {status}")
        if status != "OK":
            sys.exit("EfficientNet port failed the ImageNet sanity check.")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--out", default=str(Path.home() / ".keras" / "models"),
                        help="Keras cache folder (ResNet must be here to be found offline)")
    args = parser.parse_args()
    out = Path(args.out).expanduser()
    out.mkdir(parents=True, exist_ok=True)

    fetch(*RESNET, out / "resnet50v2_weights_tf_dim_ordering_tf_kernels_notop.h5")
    raw_top = fetch(*EFFNET["top"], out / "efficientnet-b0_noisy-student.h5")
    raw_notop = fetch(*EFFNET["notop"], out / "efficientnet-b0_noisy-student_notop.h5")

    import keras

    full = keras.applications.EfficientNetB0(include_top=True, weights=None)
    port_efficientnet(full, legacy_h5_weights(raw_top), rename={"predictions": "probs"})
    verify(full)

    backbone = keras.applications.EfficientNetB0(include_top=False, weights=None, input_shape=(224, 224, 3))
    port_efficientnet(backbone, legacy_h5_weights(raw_notop))
    for layer in backbone.layers:  # the no-top file must give the same features as the verified full model
        if layer.weights and not isinstance(layer, keras.layers.Normalization):
            same = all(np.array_equal(a, b) for a, b in zip(layer.get_weights(), full.get_layer(layer.name).get_weights()))
            if not same:
                sys.exit(f"Layer {layer.name} differs between the top and no-top files.")
    target = out / "efficientnetb0_noisy-student_notop.weights.h5"
    backbone.save_weights(target)
    print(f"saved {target}\nSet `training.effnet_weights_file: {target}` in config.yaml to use it.")


if __name__ == "__main__":
    main()
