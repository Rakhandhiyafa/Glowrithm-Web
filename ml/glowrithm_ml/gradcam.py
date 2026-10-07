"""Grad-CAM (Selvaraju et al., 2020) for single- and multi-branch Keras models.

For class c and a convolutional feature map A (k channels):
    alpha_k^c = mean_ij( d y^c / d A_ij^k )          (global-average-pooled gradients)
    L^c       = ReLU( sum_k alpha_k^c * A^k )
y^c is the pre-softmax logit, which avoids the saturated gradients of the softmax output.
For the ensemble, one map is computed per backbone (the input of each GlobalAveragePooling2D
layer), each map is normalised to [0, 1], and the maps are averaged into a fused explanation.
"""
from __future__ import annotations

import cv2
import keras
import numpy as np
import tensorflow as tf


class GradCAM:
    def __init__(self, model: keras.Model):
        gap_layers = [layer for layer in model.layers if isinstance(layer, keras.layers.GlobalAveragePooling2D)]
        if not gap_layers:
            raise ValueError("The model has no GlobalAveragePooling2D layer to attach Grad-CAM to.")
        self.branch_names = [layer.name.removesuffix("_gap") for layer in gap_layers]
        feature_maps = [layer.input for layer in gap_layers]
        logits = model.get_layer("logits").output
        self._n = len(feature_maps)
        self._grad_model = keras.Model(model.inputs, feature_maps + [logits, model.outputs[0]])

    def explain(self, batch: np.ndarray, class_index: int | None = None) -> dict:
        """batch: float32 (1, H, W, 3) in [0, 255]. Returns probabilities, class index and maps in [0, 1]."""
        x = tf.convert_to_tensor(batch, dtype=tf.float32)
        with tf.GradientTape() as tape:
            outputs = self._grad_model(x, training=False)
            feature_maps, logits, probs = outputs[: self._n], outputs[self._n], outputs[self._n + 1]
            index = int(tf.argmax(probs[0])) if class_index is None else int(class_index)
            score = logits[:, index]
        gradients = tape.gradient(score, feature_maps)

        height, width = int(x.shape[1]), int(x.shape[2])
        branch_maps = {}
        for name, fmap, grad in zip(self.branch_names, feature_maps, gradients):
            alpha = tf.reduce_mean(grad, axis=(1, 2))                                    # (1, k)
            cam = tf.nn.relu(tf.reduce_sum(fmap * alpha[:, None, None, :], axis=-1))[0]  # (h, w)
            cam = cv2.resize(cam.numpy().astype(np.float32), (width, height), interpolation=cv2.INTER_CUBIC)
            branch_maps[name] = _normalise(np.maximum(cam, 0.0))
        fused = _normalise(np.mean(list(branch_maps.values()), axis=0))
        return {
            "class_index": index,
            "probabilities": probs[0].numpy().astype(np.float64),
            "cam": fused,
            "branch_cams": branch_maps,
        }


def _normalise(cam: np.ndarray) -> np.ndarray:
    peak = float(cam.max())
    return (cam / peak).astype(np.float32) if peak > 1e-8 else np.zeros_like(cam, dtype=np.float32)


def colorize(cam: np.ndarray, size: int | None = None) -> np.ndarray:
    """Map [0, 1] activations to an RGB 'thermal' (JET) image: blue = low, red = high influence."""
    if size is not None and cam.shape[:2] != (size, size):
        cam = cv2.resize(cam, (size, size), interpolation=cv2.INTER_LINEAR)
    heat = cv2.applyColorMap(np.uint8(255 * np.clip(cam, 0.0, 1.0)), cv2.COLORMAP_JET)
    return cv2.cvtColor(heat, cv2.COLOR_BGR2RGB)


def overlay(rgb: np.ndarray, cam: np.ndarray, alpha: float = 0.45) -> np.ndarray:
    heat = colorize(cv2.resize(cam, (rgb.shape[1], rgb.shape[0]), interpolation=cv2.INTER_LINEAR))
    return cv2.addWeighted(rgb.astype(np.uint8), 1.0 - alpha, heat, alpha, 0.0)
