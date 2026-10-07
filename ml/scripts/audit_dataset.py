#!/usr/bin/env python3
"""Audit a raw image dataset before training (CD-5: dataset description and leakage check).

    python scripts/audit_dataset.py --raw data/raw/kaggle_skin --out reports/dataset_audit

Reports, per original split (train/valid/test folders, if any) and class:
  - image counts, file types, image sizes;
  - exact duplicates (MD5) and near-duplicates (256-bit difference hash within --bits, also comparing each image
    with the mirror image of the others, because horizontal flips are a common augmentation; glowrithm_ml/dedup.py);
  - copies that share a Roboflow export name (<name>_jpg.rf.<hash>.jpg: augmented copies of one source photo);
  - how many duplicate groups span more than one split (leakage: the same photo in train and test) or more than
    one class (label conflicts);
  - Haar-cascade face detection rate and face size, and the quality-gate measurements on the face crops,
    with the share of images each current threshold would reject.
Writes audit.json, audit.md and sample_grid.png (random images per class) to --out.
"""
from __future__ import annotations

import argparse
import hashlib
import random
import sys
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from glowrithm_ml.config import save_json  # noqa: E402
from glowrithm_ml.dedup import dhash256, group_duplicates, roboflow_stem  # noqa: E402
from glowrithm_ml.preprocessing import detect_face, load_image_file, resize_square, square_crop  # noqa: E402
from glowrithm_ml.quality import QualityThresholds, measure  # noqa: E402

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}
CLASS_ALIASES = {"dry": "dry", "kering": "dry", "normal": "normal", "oily": "oily", "berminyak": "oily", "oil": "oily"}
SPLIT_ALIASES = {"train": "train", "training": "train", "valid": "val", "val": "val", "validation": "val",
                 "test": "test", "testing": "test"}


def nearest(parts, aliases):
    for part in reversed(parts):
        if part.lower() in aliases:
            return aliases[part.lower()]
    return None


def describe(values) -> dict:
    arr = np.asarray(values, dtype=float)
    if arr.size == 0:
        return {}
    return {"min": float(arr.min()), "p5": float(np.percentile(arr, 5)), "median": float(np.median(arr)),
            "p95": float(np.percentile(arr, 95)), "max": float(arr.max())}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--raw", required=True, help="dataset folder (class folders may be nested in split folders)")
    parser.add_argument("--out", default="reports/dataset_audit")
    parser.add_argument("--bits", type=int, default=10, help="max 256-bit dHash distance for near-duplicates")
    parser.add_argument("--max-group", type=int, default=50, help="near-duplicate links never build a bigger group")
    parser.add_argument("--grid", type=int, default=8, help="sample images per class in sample_grid.png")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    raw = Path(args.raw).resolve()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    files = sorted(p for p in raw.rglob("*") if p.is_file() and p.suffix.lower() in IMAGE_EXTS)
    if not files:
        sys.exit(f"No images found under {raw}")
    t = QualityThresholds()

    items = []
    for n, path in enumerate(files, 1):
        rel = path.relative_to(raw)
        label = nearest(rel.parts[:-1], CLASS_ALIASES)
        split = nearest(rel.parts[:-1], SPLIT_ALIASES) or "none"
        data = path.read_bytes()
        try:
            rgb = load_image_file(path)
        except Exception as exc:  # unreadable or unsupported
            items.append({"rel": rel.as_posix(), "label": label, "split": split, "error": str(exc)})
            continue
        box = detect_face(rgb)
        crop = resize_square(square_crop(rgb, box, 0.30), 384)
        q = measure(crop)
        items.append({
            "rel": rel.as_posix(), "label": label, "split": split, "ext": path.suffix.lower(), "bytes": len(data),
            "md5": hashlib.md5(data).hexdigest(), "width": rgb.shape[1], "height": rgb.shape[0],
            "hash": dhash256(rgb), "mirror": dhash256(rgb, mirror=True), "source_stem": roboflow_stem(path.name),
            "face": box is not None, "face_ratio": (box[2] / rgb.shape[1]) if box is not None else None, **q,
        })
        if n % 250 == 0:
            print(f"  scanned {n}/{len(files)}")
    ok = [i for i in items if "error" not in i]
    print(f"{len(files)} files, {len(ok)} readable")

    # ---- duplicate groups: same bytes, same Roboflow source name, or near-identical (also mirrored) hash
    keyed = [f"md5:{i['md5']}" if i["source_stem"] is None else f"stem:{i['source_stem']}" for i in ok]
    index_groups, group_stats = group_duplicates(np.stack([i["hash"] for i in ok]), np.stack([i["mirror"] for i in ok]),
                                                 keyed, max_bits=args.bits, max_group=args.max_group)
    groups = {k: [ok[j] for j in idx] for k, idx in enumerate(index_groups)}
    multi = [g for g in groups.values() if len(g) > 1]
    cross_split = [g for g in multi if len({m["split"] for m in g}) > 1]
    conflicts = [g for g in multi if len({m["label"] for m in g}) > 1]
    exact_dupes = len(ok) - len({i["md5"] for i in ok})
    stems = Counter(i["source_stem"] for i in ok if i["source_stem"])

    # ---- tables
    splits = sorted({i["split"] for i in ok}, key=lambda s: ["train", "val", "test", "none"].index(s))
    classes = sorted({i["label"] for i in ok if i["label"]})
    counts = {s: {c: sum(1 for i in ok if i["split"] == s and i["label"] == c) for c in classes} for s in splits}
    images_in_cross_split = sum(len(g) for g in cross_split)
    test_like = [i for g in cross_split for i in g if i["split"] in ("test", "val")]
    leak = {"groups": len(cross_split), "images": images_in_cross_split,
            "val_or_test_images_with_a_copy_in_another_split": len(test_like)}
    quality = {
        "brightness": describe([i["brightness"] for i in ok]), "glare": describe([i["glare"] for i in ok]),
        "sharpness": describe([i["sharpness"] for i in ok]),
        "share_failing": {
            "brightness": float(np.mean([(i["brightness"] < t.brightness_fail[0]) or (i["brightness"] > t.brightness_fail[1]) for i in ok])),
            "glare": float(np.mean([i["glare"] > t.glare_fail for i in ok])),
            "sharpness": float(np.mean([i["sharpness"] < t.sharpness_fail for i in ok])),
            "face_size": float(np.mean([(i["face_ratio"] or 1.0) < t.face_fail for i in ok])),
        },
    }
    report = {
        "raw_dir": str(raw), "files": len(files), "readable": len(ok), "unreadable": [i["rel"] for i in items if "error" in i],
        "per_split_class": counts, "file_types": dict(Counter(i["ext"] for i in ok)),
        "width": describe([i["width"] for i in ok]), "height": describe([i["height"] for i in ok]),
        "size_examples": dict(Counter(f"{i['width']}x{i['height']}" for i in ok).most_common(5)),
        "exact_duplicate_files": exact_dupes, "near_duplicate_pairs": group_stats["near_duplicate_links"],
        "near_duplicate_links_refused": group_stats["near_duplicate_links_refused"],
        "duplicate_groups": len(multi), "images_in_duplicate_groups": sum(len(g) for g in multi),
        "largest_group": max((len(g) for g in multi), default=1),
        "roboflow_named_files": sum(stems.values()), "roboflow_sources": len(stems),
        "roboflow_sources_with_copies": sum(1 for v in stems.values() if v > 1),
        "cross_split_leakage": leak, "label_conflict_groups": len(conflicts),
        "label_conflict_examples": [[m["rel"] for m in g][:4] for g in conflicts[:5]],
        "cross_split_examples": [[f"{m['split']}:{m['rel']}" for m in g][:4] for g in cross_split[:5]],
        "face_detection_rate": float(np.mean([i["face"] for i in ok])),
        "face_detection_rate_per_class": {c: float(np.mean([i["face"] for i in ok if i["label"] == c])) for c in classes},
        "face_ratio": describe([i["face_ratio"] for i in ok if i["face_ratio"] is not None]),
        "quality": quality, "near_duplicate_bits": args.bits,
    }
    save_json(report, out / "audit.json")

    lines = [f"# Dataset audit: `{raw.name}`", "", f"{len(files)} files, {len(ok)} readable.", "",
             "| split | " + " | ".join(classes) + " | total |", "|---|" + "---|" * (len(classes) + 1)]
    for s in splits:
        lines.append(f"| {s} | " + " | ".join(str(counts[s][c]) for c in classes) + f" | {sum(counts[s].values())} |")
    lines += ["", f"- Image size (width): {report['width']}", f"- Most common sizes: {report['size_examples']}",
              f"- Exact duplicate files: {exact_dupes}; near-duplicate pairs (256-bit dHash <= {args.bits} bits, mirror-aware): "
              f"{group_stats['near_duplicate_links']} (links refused by the group-size cap: {group_stats['near_duplicate_links_refused']})",
              f"- Duplicate groups: {len(multi)} holding {report['images_in_duplicate_groups']} images (largest {report['largest_group']})",
              f"- Roboflow-named files: {report['roboflow_named_files']} from {report['roboflow_sources']} source photos",
              f"- Groups spanning more than one split: {leak['groups']} ({leak['images']} images; "
              f"{leak['val_or_test_images_with_a_copy_in_another_split']} val/test images have a copy elsewhere)",
              f"- Groups with conflicting labels: {len(conflicts)}",
              f"- Face detected (Haar): {report['face_detection_rate']:.1%}; per class {report['face_detection_rate_per_class']}",
              f"- Quality gate, share of images the current fail thresholds would reject: {quality['share_failing']}"]
    (out / "audit.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    # ---- sample grid
    rng = random.Random(args.seed)
    tile, cols = 160, args.grid
    grid = Image.new("RGB", (cols * tile, len(classes) * tile), "white")
    for r, c in enumerate(classes):
        pool = [i for i in ok if i["label"] == c]
        for k, item in enumerate(rng.sample(pool, min(cols, len(pool)))):
            img = Image.fromarray(resize_square(square_crop(load_image_file(raw / item["rel"]), None, 0.0), tile))
            grid.paste(img, (k * tile, r * tile))
    grid.save(out / "sample_grid.png")
    print("\n".join(lines))
    print(f"\nSaved {out / 'audit.json'}, audit.md and sample_grid.png (rows: {', '.join(classes)})")


if __name__ == "__main__":
    main()
