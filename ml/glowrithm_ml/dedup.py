"""Duplicate detection shared by scripts/audit_dataset.py and scripts/prepare_dataset.py.

Two images are treated as the same photo when
  - they come from one Roboflow export source (<name>_jpg.rf.<hash>.jpg: augmented copies of one photo), or
  - their 256-bit difference hashes differ in at most `max_bits` bits, also when one image is mirrored
    (horizontal flips are a common augmentation).
Groups are the connected components of these links. Near-duplicate links are not followed when they would
build a group larger than `max_group`, because chains of loose matches between similar-looking photos could
otherwise merge unrelated people and break the stratified split; the number of refused links is reported.
"""
from __future__ import annotations

import re
from pathlib import Path

import numpy as np
from PIL import Image

ROBOFLOW = re.compile(r"^(?P<stem>.+?)_(?:jpe?g|png|bmp|webp)\.rf\.[0-9a-f]{8,}$", re.IGNORECASE)
HASH_SIZE = 16  # 16 x 16 differences = 256 bits


def roboflow_stem(filename: str) -> str | None:
    match = ROBOFLOW.match(Path(filename).stem)
    return match.group("stem").lower() if match else None


def dhash256(rgb: np.ndarray, mirror: bool = False) -> np.ndarray:
    """256-bit difference hash as four uint64 words."""
    gray = Image.fromarray(rgb).convert("L")
    if mirror:
        gray = gray.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
    pixels = np.asarray(gray.resize((HASH_SIZE + 1, HASH_SIZE), Image.Resampling.LANCZOS), dtype=np.int16)
    bits = (pixels[:, 1:] > pixels[:, :-1]).astype(np.uint8).flatten()
    return np.packbits(bits).view(">u8").astype(np.uint64)


def hamming(words: np.ndarray, one: np.ndarray) -> np.ndarray:
    """Bit distance between each row of `words` (n, 4) and `one` (4,)."""
    xor = np.bitwise_xor(words, one[None, :]).astype(">u8")
    return np.unpackbits(xor.view(np.uint8).reshape(len(words), -1), axis=1).sum(axis=1)


def group_duplicates(hashes: np.ndarray, mirrors: np.ndarray, stems: list[str | None], max_bits: int = 10,
                     max_group: int = 50) -> tuple[list[list[int]], dict]:
    """Return (groups as index lists, stats). hashes/mirrors: (n, 4) uint64 arrays."""
    n = len(stems)
    parent = list(range(n))
    size = [1] * n

    def find(i: int) -> int:
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    def union(a: int, b: int, limit: int | None = None) -> bool:
        ra, rb = find(a), find(b)
        if ra == rb:
            return True
        if limit is not None and size[ra] + size[rb] > limit:
            return False
        parent[rb] = ra
        size[ra] += size[rb]
        return True

    first: dict[str, int] = {}
    for k, stem in enumerate(stems):
        if stem is None:
            continue
        if stem in first:
            union(first[stem], k)
        else:
            first[stem] = k
    near_links = refused = 0
    for k in range(n - 1):
        rest = slice(k + 1, None)
        dist = np.minimum(hamming(hashes[rest], hashes[k]), hamming(mirrors[rest], hashes[k]))
        for j in np.nonzero(dist <= max_bits)[0]:
            near_links += 1
            if not union(k, k + 1 + int(j), limit=max_group):
                refused += 1
    groups: dict[int, list[int]] = {}
    for k in range(n):
        groups.setdefault(find(k), []).append(k)
    out = list(groups.values())
    stats = {"near_duplicate_links": near_links, "near_duplicate_links_refused": refused,
             "source_name_files": sum(1 for s in stems if s), "groups_with_copies": sum(1 for g in out if len(g) > 1),
             "largest_group": max(len(g) for g in out) if out else 0}
    return out, stats
