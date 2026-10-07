"""Evaluation metrics and plots used for the CD-5 test reports.

Per class c (one-vs-rest, from the K x K confusion matrix):
    Accuracy  = (TP + TN) / (TP + TN + FP + FN)        (CD-3 Eq. 3.5; overall accuracy = trace / N)
    Precision = TP / (TP + FP)                         (Eq. 3.6)
    Recall    = TP / (TP + FN)                         (Eq. 3.7)
    F1        = 2 * Precision * Recall / (Precision + Recall)   (Eq. 3.8)
Macro averages weight every class equally; weighted averages use class support.
"""
from __future__ import annotations

import csv
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from sklearn.metrics import confusion_matrix, roc_auc_score, roc_curve  # noqa: E402


def _safe_div(a: float, b: float) -> float:
    return float(a) / float(b) if b else 0.0


def wilson_interval(successes: int, n: int, z: float = 1.96) -> tuple[float, float]:
    """95% Wilson score interval of a proportion such as accuracy; reliable for small test sets."""
    if n == 0:
        return 0.0, 0.0
    p = successes / n
    denom = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / denom
    half = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return float(centre - half), float(centre + half)


def compute_metrics(y_true: np.ndarray, y_prob: np.ndarray, class_names: list[str]) -> dict:
    k = len(class_names)
    y_pred = y_prob.argmax(axis=1)
    cm = confusion_matrix(y_true, y_pred, labels=list(range(k)))
    total = int(cm.sum())
    per_class = []
    for i, name in enumerate(class_names):
        tp = int(cm[i, i])
        fp = int(cm[:, i].sum() - tp)
        fn = int(cm[i, :].sum() - tp)
        tn = total - tp - fp - fn
        precision, recall = _safe_div(tp, tp + fp), _safe_div(tp, tp + fn)
        per_class.append({
            "class": name, "support": int(cm[i, :].sum()), "tp": tp, "fp": fp, "fn": fn, "tn": tn,
            "accuracy_ovr": _safe_div(tp + tn, total), "precision": precision, "recall": recall,
            "f1": _safe_div(2 * precision * recall, precision + recall),
        })
    support = np.array([c["support"] for c in per_class], dtype=float)

    def average(key: str, weighted: bool) -> float:
        values = np.array([c[key] for c in per_class])
        return float((values * support).sum() / support.sum()) if weighted and support.sum() else float(values.mean())

    try:
        auc = float(roc_auc_score(y_true, y_prob, multi_class="ovr", average="macro", labels=list(range(k))))
    except ValueError:  # a class is missing from y_true
        auc = None
    return {
        "n_samples": total,
        "accuracy": _safe_div(np.trace(cm), total),
        "accuracy_ci95": wilson_interval(int(np.trace(cm)), total),
        "macro": {m: average(m, False) for m in ("precision", "recall", "f1")},
        "weighted": {m: average(m, True) for m in ("precision", "recall", "f1")},
        "roc_auc_ovr_macro": auc,
        "per_class": per_class,
        "confusion_matrix": cm.tolist(),
        "class_names": class_names,
    }


def plot_confusion_matrix(cm, class_names, path, normalize: bool = False, title: str | None = None) -> None:
    cm = np.asarray(cm, dtype=float)
    data = cm / np.maximum(cm.sum(axis=1, keepdims=True), 1) if normalize else cm
    fig, ax = plt.subplots(figsize=(5.2, 4.4), dpi=150)
    image = ax.imshow(data, cmap="Greens", vmin=0, vmax=1 if normalize else None)
    fig.colorbar(image, ax=ax, fraction=0.046, pad=0.04)
    ax.set(xticks=range(len(class_names)), yticks=range(len(class_names)),
           xticklabels=class_names, yticklabels=class_names, xlabel="Predicted label", ylabel="True label",
           title=title or ("Normalized confusion matrix" if normalize else "Confusion matrix"))
    threshold = data.max() / 2 if data.size else 0
    for i in range(data.shape[0]):
        for j in range(data.shape[1]):
            text = f"{data[i, j]:.2f}" if normalize else f"{int(data[i, j])}"
            ax.text(j, i, text, ha="center", va="center", color="white" if data[i, j] > threshold else "black")
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def plot_roc(y_true, y_prob, class_names, path) -> None:
    fig, ax = plt.subplots(figsize=(5.2, 4.4), dpi=150)
    for i, name in enumerate(class_names):
        positives = (np.asarray(y_true) == i).astype(int)
        if positives.min() == positives.max():
            continue
        fpr, tpr, _ = roc_curve(positives, y_prob[:, i])
        ax.plot(fpr, tpr, label=f"{name} (AUC = {roc_auc_score(positives, y_prob[:, i]):.3f})")
    ax.plot([0, 1], [0, 1], "k--", linewidth=0.8)
    ax.set(xlabel="False positive rate", ylabel="True positive rate", title="ROC curves (one-vs-rest)")
    ax.legend(loc="lower right")
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def merge_histories(csv_paths, out_path) -> dict[str, list[float]]:
    """Concatenate the per-phase CSVLogger files into one history (missing values -> NaN)."""
    rows = []
    for path in csv_paths:
        if Path(path).exists():
            with open(path, newline="", encoding="utf-8") as fh:
                rows.extend(csv.DictReader(fh))
    keys = sorted({key for row in rows for key in row})
    history = {key: [float(row[key]) if row.get(key) not in (None, "") else float("nan") for row in rows] for key in keys}
    with open(out_path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=keys)
        writer.writeheader()
        writer.writerows(rows)
    return history


def plot_history(history: dict[str, list[float]], path, finetune_start: int | None = None) -> None:
    panels = [m for m in ("loss", "accuracy", "macro_f1") if m in history]
    fig, axes = plt.subplots(1, len(panels), figsize=(4.6 * len(panels), 3.6), dpi=150)
    axes = np.atleast_1d(axes)
    epochs = np.arange(1, len(history[panels[0]]) + 1)
    for ax, metric in zip(axes, panels):
        ax.plot(epochs, history[metric], label="train")
        if f"val_{metric}" in history:
            ax.plot(epochs, history[f"val_{metric}"], label="validation")
        if finetune_start:
            ax.axvline(finetune_start + 0.5, color="grey", linestyle="--", linewidth=0.8, label="fine-tuning starts")
        ax.set(title=metric.replace("_", " "), xlabel="epoch")
        ax.grid(alpha=0.3)
    axes[0].legend()
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def write_per_class_csv(metrics: dict, path) -> None:
    fields = ["class", "support", "tp", "fp", "fn", "tn", "accuracy_ovr", "precision", "recall", "f1"]
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        for row in metrics["per_class"]:
            writer.writerow({k: (round(v, 4) if isinstance(v, float) else v) for k, v in row.items()})


def format_summary(metrics: dict) -> str:
    lines = [f"Samples: {metrics['n_samples']}   Accuracy: {metrics['accuracy']:.4f}   "
             f"Macro-F1: {metrics['macro']['f1']:.4f}   ROC-AUC: {metrics['roc_auc_ovr_macro'] or 'n/a'}",
             f"{'class':<8}{'support':>8}{'precision':>11}{'recall':>9}{'f1':>8}"]
    for row in metrics["per_class"]:
        lines.append(f"{row['class']:<8}{row['support']:>8}{row['precision']:>11.4f}{row['recall']:>9.4f}{row['f1']:>8.4f}")
    return "\n".join(lines)
