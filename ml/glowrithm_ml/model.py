"""Model builders for the Glowrithm classifier (CD-3, solution 1: homogeneous multimodel ensemble CNN).

    image (RGB 0..255) --+-- Rescaling(1/127.5, -1) -- ResNet50V2 --- GAP (2048) --+
                         |                                                       +-- concat (3328) -- Dropout
                         +-- EfficientNetB0 (built-in normalisation) -- GAP (1280) +      -- Dense 256 ReLU -- Dropout
                                                                                         -- Dense 3 (logits) -- softmax
The input of each GlobalAveragePooling2D layer is the last convolutional feature map of a backbone,
which is where Grad-CAM attaches (see gradcam.py).
"""
from __future__ import annotations

import keras
import numpy as np
from keras import layers

RESNETS = {
    "ResNet50V2": keras.applications.ResNet50V2,
    "ResNet101V2": keras.applications.ResNet101V2,
}
EFFNETS = {
    "EfficientNetB0": keras.applications.EfficientNetB0,
    "EfficientNetB1": keras.applications.EfficientNetB1,
    "EfficientNetB2": keras.applications.EfficientNetB2,
    "EfficientNetB3": keras.applications.EfficientNetB3,
}


def _resnet_branch(inputs, variant: str, weights, img_size: int):
    base = RESNETS[variant](include_top=False, weights=weights, input_shape=(img_size, img_size, 3))
    x = layers.Rescaling(1.0 / 127.5, offset=-1.0, name="resnet_preprocess")(inputs)  # = resnet_v2.preprocess_input
    feature_map = base(x, training=False)  # training=False keeps BatchNorm in inference mode while fine-tuning
    return base, layers.GlobalAveragePooling2D(name="resnet_gap")(feature_map)


def _effnet_branch(inputs, variant: str, weights, img_size: int, weights_file: str | None = None):
    if weights == "imagenet" and weights_file:  # offline alternative, see scripts/fetch_offline_weights.py
        base = EFFNETS[variant](include_top=False, weights=None, input_shape=(img_size, img_size, 3))
        base.load_weights(str(weights_file))
    else:
        base = EFFNETS[variant](include_top=False, weights=weights, input_shape=(img_size, img_size, 3))
    feature_map = base(inputs, training=False)  # Keras EfficientNet rescales/normalises 0..255 internally
    return base, layers.GlobalAveragePooling2D(name="effnet_gap")(feature_map)


def build_model(arch: str = "ensemble", num_classes: int = 3, img_size: int = 224, weights="imagenet",
                resnet_variant: str = "ResNet50V2", effnet_variant: str = "EfficientNetB0",
                dropout_1: float = 0.4, dense_units: int = 256, dropout_2: float = 0.3, l2: float = 1e-4,
                effnet_weights_file: str | None = None):
    """Return (model, backbones). arch: 'ensemble' (both backbones), 'resnet' or 'effnet' (baselines).
    effnet_weights_file: optional local EfficientNet weights used instead of the Keras download."""
    if arch not in ("ensemble", "resnet", "effnet"):
        raise ValueError(f"Unknown arch '{arch}'")
    inputs = keras.Input(shape=(img_size, img_size, 3), name="image")
    backbones, features = [], []
    if arch in ("ensemble", "resnet"):
        base, vector = _resnet_branch(inputs, resnet_variant, weights, img_size)
        backbones.append(base)
        features.append(vector)
    if arch in ("ensemble", "effnet"):
        base, vector = _effnet_branch(inputs, effnet_variant, weights, img_size, effnet_weights_file)
        backbones.append(base)
        features.append(vector)

    x = layers.Concatenate(name="feature_concat")(features) if len(features) > 1 else features[0]
    x = layers.Dropout(dropout_1, name="dropout_1")(x)
    x = layers.Dense(dense_units, activation="relu", kernel_regularizer=keras.regularizers.l2(l2), name="fc")(x)
    x = layers.Dropout(dropout_2, name="dropout_2")(x)
    logits = layers.Dense(num_classes, name="logits")(x)          # Grad-CAM differentiates these scores
    probs = layers.Activation("softmax", dtype="float32", name="probs")(logits)
    return keras.Model(inputs, probs, name=f"glowrithm_{arch}"), backbones


def set_backbones_trainable(backbones, unfreeze_fraction: float) -> None:
    """Freeze each backbone except its top `unfreeze_fraction` of layers; BatchNorm layers stay frozen."""
    for base in backbones:
        base.trainable = unfreeze_fraction > 0
        if not base.trainable:
            continue
        start = int(len(base.layers) * (1.0 - unfreeze_fraction))
        for i, layer in enumerate(base.layers):
            layer.trainable = i >= start and not isinstance(layer, layers.BatchNormalization)


def count_params(model) -> tuple[int, int]:
    trainable = int(sum(np.prod(w.shape) for w in model.trainable_weights))
    frozen = int(sum(np.prod(w.shape) for w in model.non_trainable_weights))
    return trainable, frozen


def build_demo_model(num_classes: int = 3, img_size: int = 224):
    """Tiny untrained two-branch CNN with the same interface (two GAP branches + logits/probs).
    Only for exercising the API and the app before the real model is trained."""
    inputs = keras.Input(shape=(img_size, img_size, 3), name="image")
    x = layers.Rescaling(1.0 / 255.0)(inputs)
    branches = []
    for prefix in ("demo_a", "demo_b"):
        y = x
        for i, filters in enumerate((8, 16, 32)):
            y = layers.Conv2D(filters, 3, strides=2, padding="same", activation="relu", name=f"{prefix}_conv{i}")(y)
        branches.append(layers.GlobalAveragePooling2D(name=f"{prefix}_gap")(y))
    x = layers.Concatenate(name="feature_concat")(branches)
    logits = layers.Dense(num_classes, name="logits")(x)
    probs = layers.Activation("softmax", dtype="float32", name="probs")(logits)
    return keras.Model(inputs, probs, name="glowrithm_demo")
