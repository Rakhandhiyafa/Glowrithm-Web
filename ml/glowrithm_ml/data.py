"""Dataset utilities: manifest loading, tf.data pipelines, augmentation and class balancing."""
from __future__ import annotations

import csv
from pathlib import Path

import keras
import numpy as np
import tensorflow as tf

AUTOTUNE = tf.data.AUTOTUNE


def read_manifest(path: str | Path) -> list[dict[str, str]]:
    with Path(path).open("r", encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def load_split(manifest_path: str | Path, split: str, class_names: list[str]) -> tuple[np.ndarray, np.ndarray]:
    """Return absolute image paths and integer labels for one split (train / val / test)."""
    base = Path(manifest_path).parent
    rows = [row for row in read_manifest(manifest_path) if row["split"] == split]
    paths = np.array([str(base / row["path"]) for row in rows], dtype=str)
    labels = np.array([class_names.index(row["label"]) for row in rows], dtype=np.int32)
    return paths, labels


def count_per_class(labels: np.ndarray, n_classes: int) -> np.ndarray:
    return np.bincount(labels, minlength=n_classes)


def class_weights(labels: np.ndarray, n_classes: int) -> dict[int, float]:
    """w_c = N / (K * n_c): rare classes weigh more in the loss."""
    counts = count_per_class(labels, n_classes)
    total = counts.sum()
    return {c: float(total / (n_classes * counts[c])) if counts[c] else 0.0 for c in range(n_classes)}


def _loader(img_size: int, n_classes: int):
    def load(path, label):
        raw = tf.io.read_file(path)
        img = tf.io.decode_image(raw, channels=3, expand_animations=False)
        img = tf.image.resize(tf.cast(img, tf.float32), (img_size, img_size), method="bilinear", antialias=True)
        return img, tf.one_hot(label, n_classes)
    return load


def build_augmenter(aug: dict, seed: int) -> keras.Sequential:
    """Random geometric + photometric changes that mimic real phone photos (pose, framing, light)."""
    layers = []
    if aug.get("horizontal_flip"):
        layers.append(keras.layers.RandomFlip("horizontal", seed=seed))
    if aug.get("rotation"):
        layers.append(keras.layers.RandomRotation(aug["rotation"], fill_mode="reflect", seed=seed))
    if aug.get("zoom"):
        layers.append(keras.layers.RandomZoom((-aug["zoom"], aug["zoom"]), fill_mode="reflect", seed=seed))
    if aug.get("translation"):
        layers.append(keras.layers.RandomTranslation(aug["translation"], aug["translation"], fill_mode="reflect", seed=seed))
    if aug.get("brightness"):
        layers.append(keras.layers.RandomBrightness(aug["brightness"], value_range=(0.0, 255.0), seed=seed))
    if aug.get("contrast"):
        layers.append(keras.layers.RandomContrast(aug["contrast"], seed=seed))
    return keras.Sequential(layers, name="augmentation")


def make_train_dataset(paths: np.ndarray, labels: np.ndarray, cfg: dict) -> tuple[tf.data.Dataset, int | None]:
    """Shuffled, augmented, batched training data.

    balance_strategy == "oversample": every class is drawn with equal probability
    (resampling, CD-2); one epoch = as many samples as K x the largest class.
    Returns (dataset, steps_per_epoch); steps is None when the dataset is finite.
    """
    data_cfg, train_cfg = cfg["data"], cfg["training"]
    n_classes = len(cfg["project"]["class_names"])
    seed, batch = cfg["project"]["seed"], train_cfg["batch_size"]
    load = _loader(data_cfg["img_size"], n_classes)

    steps = None
    if train_cfg.get("balance_strategy") == "oversample":
        per_class, counts = [], count_per_class(labels, n_classes)
        for c in range(n_classes):
            idx = np.where(labels == c)[0]
            if len(idx) == 0:
                continue
            ds_c = tf.data.Dataset.from_tensor_slices((paths[idx], labels[idx]))
            per_class.append(ds_c.shuffle(len(idx), seed=seed, reshuffle_each_iteration=True).repeat())
        ds = tf.data.Dataset.sample_from_datasets(per_class, weights=[1.0 / len(per_class)] * len(per_class), seed=seed)
        steps = int(np.ceil(counts.max() * len(per_class) / batch))
    else:
        ds = tf.data.Dataset.from_tensor_slices((paths, labels)).shuffle(len(paths), seed=seed, reshuffle_each_iteration=True)

    augmenter = build_augmenter(cfg.get("augmentation", {}), seed)

    def augment(x, y):
        return tf.clip_by_value(augmenter(x, training=True), 0.0, 255.0), y

    ds = ds.map(load, num_parallel_calls=AUTOTUNE).batch(batch).map(augment, num_parallel_calls=AUTOTUNE)
    return ds.prefetch(AUTOTUNE), steps


def make_eval_dataset(paths: np.ndarray, labels: np.ndarray, cfg: dict, img_size: int | None = None,
                      batch_size: int | None = None) -> tf.data.Dataset:
    """Deterministic (unshuffled, unaugmented) pipeline for validation / testing."""
    n_classes = len(cfg["project"]["class_names"])
    load = _loader(img_size or cfg["data"]["img_size"], n_classes)
    ds = tf.data.Dataset.from_tensor_slices((paths, labels)).map(load, num_parallel_calls=AUTOTUNE)
    return ds.batch(batch_size or cfg["training"]["batch_size"]).prefetch(AUTOTUNE)
