#!/usr/bin/env python3
"""Field validation on a local test set (CD-5): volunteers' photos with blotting-paper reference labels.

    python scripts/evaluate_local.py --model artifacts/ensemble/model.keras \
        --csv data/local_test/labels.csv --images data/local_test/photos

CSV columns (template: ml/templates/local_test_labels.csv): participant_id, photo_file, lighting (alami / lampu /
redup), lux, blot_forehead, blot_nose, blot_left_cheek, blot_right_cheek (0 no oil, 1 light, 2 clear), tight,
flaky (0/1), reference_label (optional; derived from the blotting scores when empty, see derive_label).
Reports accuracy with a 95% Wilson interval, macro-F1, Cohen's kappa against the reference, results per lighting
condition, how often a participant keeps the prediction made under the reference lighting, and the photos the
quality gate would reject. Combination-skin participants are counted but excluded from the 3-class metrics.
See docs/PROTOKOL_DATA_UJI_LOKAL.md for the data-collection protocol.
"""
from __future__ import annotations

import argparse
import csv
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np
from sklearn.metrics import cohen_kappa_score

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import keras  # noqa: E402

from glowrithm_ml.config import load_json, meta_path_for, save_json  # noqa: E402
from glowrithm_ml.metrics import compute_metrics, plot_confusion_matrix, wilson_interval  # noqa: E402
from glowrithm_ml.preprocessing import load_image_file, preprocess_for_model  # noqa: E402
from glowrithm_ml.quality import assess_quality  # noqa: E402

KAPPA_SCALE = [(0.0, "poor"), (0.2, "slight"), (0.4, "fair"), (0.6, "moderate"), (0.8, "substantial"), (1.01, "almost perfect")]


def derive_label(row: dict) -> str:
    """Blotting-paper rubric from docs/PROTOKOL_DATA_UJI_LOKAL.md (team heuristic: confirm with an expert)."""
    def score(key: str) -> int:
        return int(row.get(key) or 0)

    t_zone = max(score("blot_forehead"), score("blot_nose"))
    cheeks = max(score("blot_left_cheek"), score("blot_right_cheek"))
    if t_zone >= 1 and cheeks >= 1:
        return "oily"
    if t_zone >= 2 and cheeks == 0:
        return "combination"
    if t_zone == 0 and cheeks == 0 and (score("tight") or score("flaky")):
        return "dry"
    return "normal"


def accuracy_of(records: list[dict]) -> dict:
    correct = sum(r["pred"] == r["reference"] for r in records)
    return {"n": len(records), "accuracy": correct / len(records) if records else None,
            "ci95": wilson_interval(correct, len(records))}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--model", required=True)
    parser.add_argument("--csv", required=True)
    parser.add_argument("--images", required=True)
    parser.add_argument("--reference-lighting", default="alami")
    parser.add_argument("--out", help="default: <model folder>/reports/local")
    args = parser.parse_args()

    meta = load_json(meta_path_for(args.model))
    names = meta["class_names"]
    model = keras.saving.load_model(args.model, compile=False)
    with open(args.csv, newline="", encoding="utf-8") as fh:
        rows = [r for r in csv.DictReader(fh) if (r.get("photo_file") or "").strip()]
    out_dir = Path(args.out) if args.out else Path(args.model).parent / "reports" / "local"
    out_dir.mkdir(parents=True, exist_ok=True)

    records = []
    for row in rows:
        rgb = load_image_file(Path(args.images) / row["photo_file"])
        prepared = preprocess_for_model(rgb, crop_faces=meta["crop_faces"], margin=meta["face_margin"],
                                        processed_size=meta["processed_size"], img_size=meta["img_size"])
        quality = assess_quality(prepared.display, rgb.shape[:2], prepared.face_box)
        probs = np.asarray(model.predict_on_batch(prepared.model_input[None]))[0]
        records.append({"participant_id": row["participant_id"], "photo_file": row["photo_file"],
                        "lighting": (row.get("lighting") or "").strip().lower(), "lux": row.get("lux", ""),
                        "reference": (row.get("reference_label") or "").strip().lower() or derive_label(row),
                        "pred": names[int(probs.argmax())], "confidence": float(probs.max()),
                        "quality_passed": quality["passed"], "probs": probs})

    usable = [r for r in records if r["reference"] in names]
    if not usable:
        sys.exit("No photo has a dry / normal / oily reference label.")
    y_true = np.array([names.index(r["reference"]) for r in usable])
    probs = np.stack([r["probs"] for r in usable])
    metrics = compute_metrics(y_true, probs, names)
    kappa = float(cohen_kappa_score(y_true, probs.argmax(axis=1), labels=list(range(len(names)))))
    by_participant: dict[str, dict[str, str]] = defaultdict(dict)
    for r in records:
        by_participant[r["participant_id"]][r["lighting"]] = r["pred"]
    consistency: dict[str, list[bool]] = defaultdict(list)
    for preds in by_participant.values():
        reference = preds.get(args.reference_lighting)
        for light, pred in preds.items():
            if reference is not None and light != args.reference_lighting:
                consistency[light].append(pred == reference)
    summary = {
        "n_photos": len(records), "n_participants": len(by_participant),
        "n_combination_excluded": sum(r["reference"] == "combination" for r in records),
        "accuracy": metrics["accuracy"], "accuracy_ci95": metrics["accuracy_ci95"], "macro_f1": metrics["macro"]["f1"],
        "cohen_kappa": kappa, "kappa_label": next(label for limit, label in KAPPA_SCALE if kappa < limit),
        "per_lighting": {light: accuracy_of([r for r in usable if r["lighting"] == light])
                         for light in sorted({r["lighting"] for r in usable})},
        "same_prediction_as_reference_lighting": {light: {"n": len(v), "share": float(np.mean(v))}
                                                  for light, v in consistency.items()},
        "quality_gate": {"passed": accuracy_of([r for r in usable if r["quality_passed"]]),
                         "rejected": accuracy_of([r for r in usable if not r["quality_passed"]])},
        "confusion_matrix": metrics["confusion_matrix"], "class_names": names,
    }
    save_json(summary, out_dir / "local_metrics.json")
    with open(out_dir / "local_predictions.csv", "w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(["participant_id", "photo_file", "lighting", "lux", "reference", "pred", "confidence", "quality_passed"])
        for r in records:
            writer.writerow([r["participant_id"], r["photo_file"], r["lighting"], r["lux"], r["reference"], r["pred"],
                             f"{r['confidence']:.4f}", int(r["quality_passed"])])
    plot_confusion_matrix(metrics["confusion_matrix"], names, out_dir / "confusion_matrix_local.png",
                          title="Local test set vs blotting-paper reference")
    lo, hi = metrics["accuracy_ci95"]
    print(f"{len(records)} photos of {len(by_participant)} participants ({summary['n_combination_excluded']} combination excluded)")
    print(f"Accuracy {metrics['accuracy']:.2%} (95% CI {lo:.2%}-{hi:.2%}), macro-F1 {metrics['macro']['f1']:.4f}, "
          f"Cohen's kappa {kappa:.3f} ({summary['kappa_label']})")
    for light, s in summary["per_lighting"].items():
        print(f"  {light or '(no lighting given)'}: n={s['n']} accuracy {s['accuracy']:.2%}")
    print(f"Saved {out_dir}")


if __name__ == "__main__":
    main()
