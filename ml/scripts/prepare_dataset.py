#!/usr/bin/env python3
"""Build a clean, leakage-free, face-cropped dataset and manifest.csv from raw class folders.

    python scripts/prepare_dataset.py --config config.yaml
    python scripts/prepare_dataset.py --config config.yaml --keep-existing-split

Steps
  1. discover images under paths.raw_dir; the class is the nearest folder named dry/normal/oily
     (Indonesian names kering/berminyak also work)
  2. deduplicate: identical files (MD5) are kept once; near-identical images (256-bit difference hash within
     data.near_duplicate_bits, also against the mirror image) and copies exported from one source photo
     (Roboflow names <name>_jpg.rf.<hash>.jpg) form a group that always lands in ONE split, so test images
     never leak into training (see glowrithm_ml/dedup.py); groups whose members carry different labels are
     dropped as label noise
  3. detect the face (Haar cascade), square-crop it with a margin and save a processed_size JPEG
  4. stratified, group-aware split (70/15/15 by default) -> manifest.csv + summary.json
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import os
import random
import sys
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from glowrithm_ml.config import load_config, save_json  # noqa: E402
from glowrithm_ml.dedup import dhash256, group_duplicates, roboflow_stem  # noqa: E402
from glowrithm_ml.preprocessing import load_image_file, prepare_face, resize_square  # noqa: E402

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}
CLASS_ALIASES = {"dry": "dry", "kering": "dry", "normal": "normal", "oily": "oily", "berminyak": "oily", "oil": "oily"}
SPLIT_ALIASES = {"train": "train", "training": "train", "valid": "val", "val": "val",
                 "validation": "val", "test": "test", "testing": "test"}
SPLIT_PRIORITY = {"train": 0, "val": 1, "test": 2}


def infer_label(rel: Path) -> str | None:
    for part in reversed(rel.parts[:-1]):
        label = CLASS_ALIASES.get(part.lower())
        if label:
            return label
    return None


def infer_split(rel: Path) -> str | None:
    for part in rel.parts[:-1]:
        split = SPLIT_ALIASES.get(part.lower())
        if split:
            return split
    return None


def assign_group_splits(groups: dict[str, list[dict]], ratios: dict[str, float], seed: int) -> None:
    """Greedy stratified split: each label's groups go to the split with the largest remaining deficit."""
    by_label: dict[str, list[str]] = defaultdict(list)
    for gid, members in groups.items():
        by_label[members[0]["label"]].append(gid)
    rng = random.Random(seed)
    for label, gids in by_label.items():
        rng.shuffle(gids)
        total = sum(len(groups[g]) for g in gids)
        filled = {s: 0 for s in ratios}
        for gid in gids:
            split = max(ratios, key=lambda s: ratios[s] * total - filled[s])
            filled[split] += len(groups[gid])
            for item in groups[gid]:
                item["split"] = split


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--config", default="config.yaml")
    parser.add_argument("--raw", help="override paths.raw_dir")
    parser.add_argument("--keep-existing-split", action="store_true", help="use the dataset's train/valid/test folders")
    args = parser.parse_args()

    cfg = load_config(args.config)
    dcfg, seed = cfg["data"], cfg["project"]["seed"]
    raw_dir = Path(args.raw or cfg["paths"]["raw_dir"]).resolve()
    out_dir = Path(cfg["paths"]["processed_dir"])
    manifest_path = Path(cfg["paths"]["manifest"])
    keep_split = args.keep_existing_split or dcfg.get("keep_existing_split", False)
    if not raw_dir.exists():
        sys.exit(f"Raw dataset folder not found: {raw_dir}")

    files = sorted(p for p in raw_dir.rglob("*") if p.suffix.lower() in IMAGE_EXTS and p.is_file())
    print(f"Found {len(files)} image files under {raw_dir}")

    items, seen_md5 = [], set()
    stats = Counter()
    for n, path in enumerate(files, 1):
        rel = path.relative_to(raw_dir)
        label = infer_label(rel)
        if label is None:
            stats["skipped_no_label"] += 1
            continue
        data = path.read_bytes()
        md5 = hashlib.md5(data).hexdigest()
        if dcfg.get("dedupe", True) and md5 in seen_md5:
            stats["exact_duplicates_removed"] += 1
            continue
        seen_md5.add(md5)
        try:
            rgb = load_image_file(path)
        except Exception as exc:  # corrupted / unsupported file
            print(f"  ! skipped unreadable file {rel}: {exc}")
            stats["unreadable"] += 1
            continue
        items.append({"source": rel.as_posix(), "label": label, "md5": md5, "hash": dhash256(rgb),
                      "mirror": dhash256(rgb, mirror=True), "stem": roboflow_stem(rel.name),
                      "orig_split": infer_split(rel)})  # pixels are re-read later to keep memory low
        if n % 200 == 0:
            print(f"  scanned {n}/{len(files)}")

    # Near-duplicate groups. Mixed-label groups are label noise -> drop them.
    if dcfg.get("dedupe", True) and items:
        index_groups, group_stats = group_duplicates(
            np.stack([i["hash"] for i in items]), np.stack([i["mirror"] for i in items]),
            [i["stem"] if dcfg.get("group_by_source_name", True) else None for i in items],
            max_bits=int(dcfg.get("near_duplicate_bits", 10)), max_group=int(dcfg.get("max_group_size", 50)))
        stats.update({key: value for key, value in group_stats.items() if key != "groups_with_copies"})
        found_groups = [[items[k] for k in idx] for idx in index_groups]
    else:
        found_groups = [[item] for item in items]
    groups: dict[str, list[dict]] = {f"g{k:05d}_{members[0]['md5'][:8]}": members for k, members in enumerate(found_groups)}
    for gid in list(groups):
        if len({m["label"] for m in groups[gid]}) > 1:
            stats["conflicting_label_images_removed"] += len(groups.pop(gid))
    stats["near_duplicate_groups"] = sum(1 for g in groups.values() if len(g) > 1)
    stats["images_in_near_duplicate_groups"] = sum(len(g) for g in groups.values() if len(g) > 1)

    if keep_split:
        for gid, members in groups.items():
            if any(m["orig_split"] is None for m in members):
                sys.exit(f"--keep-existing-split: {members[0]['source']} is not inside a train/valid/test folder")
            best = min((m["orig_split"] for m in members), key=SPLIT_PRIORITY.get)
            kept = [m for m in members if m["orig_split"] == best]  # drop copies that would leak across splits
            stats["cross_split_duplicates_removed"] += len(members) - len(kept)
            for m in kept:
                m["split"] = best
            groups[gid] = kept
    else:
        assign_group_splits(groups, dcfg["split"], seed)

    out_dir.mkdir(parents=True, exist_ok=True)
    rows = []
    for gid, members in groups.items():
        for m in members:
            rgb = load_image_file(raw_dir / m["source"])
            square, found = prepare_face(rgb, dcfg["crop_faces"], dcfg["face_margin"])
            crop = resize_square(square, dcfg["processed_size"])
            target = out_dir / m["label"] / f"{Path(m['source']).stem}_{m['md5'][:8]}.jpg"
            target.parent.mkdir(parents=True, exist_ok=True)
            Image.fromarray(crop).save(target, quality=95)
            rows.append({"path": Path(os.path.relpath(target, manifest_path.parent)).as_posix(), "label": m["label"],
                         "split": m["split"], "group": gid, "face_found": int(found), "source": m["source"]})
            stats["faces_found" if found else "faces_not_found"] += 1

    rows.sort(key=lambda r: (r["split"], r["label"], r["path"]))
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    with manifest_path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=["path", "label", "split", "group", "face_found", "source"])
        writer.writeheader()
        writer.writerows(rows)

    table = {split: dict(Counter(r["label"] for r in rows if r["split"] == split)) for split in ("train", "val", "test")}
    detected = stats["faces_found"] / max(1, len(rows))
    summary = {"raw_files": len(files), "kept_images": len(rows), "per_split": table,
               "face_detection_rate": round(detected, 4), "stats": dict(stats)}
    save_json(summary, manifest_path.with_name("summary.json"))

    print("\nImages per split and class:")
    print(f"{'split':<7}" + "".join(f"{c:>9}" for c in cfg["project"]["class_names"]) + f"{'total':>9}")
    for split, counts in table.items():
        print(f"{split:<7}" + "".join(f"{counts.get(c, 0):>9}" for c in cfg["project"]["class_names"])
              + f"{sum(counts.values()):>9}")
    print(f"\nFace detected in {detected:.1%} of images. Other stats: {dict(stats)}")
    print(f"Manifest: {manifest_path}")


if __name__ == "__main__":
    main()
