from __future__ import annotations

import hashlib
from collections.abc import Iterable


def stable_split(group_key: str, train: float = 0.8, val: float = 0.1) -> str:
    """Assign a group deterministically; all samples from a board group stay together."""
    if train <= 0 or val < 0 or train + val >= 1:
        raise ValueError("Split ratios must leave a non-zero test partition")
    bucket = int(hashlib.sha256(group_key.encode("utf-8")).hexdigest()[:8], 16) / 0xFFFFFFFF
    if bucket < train:
        return "train"
    if bucket < train + val:
        return "val"
    return "test"


def board_group(stem: str) -> str:
    compact = stem.removesuffix("_test").removesuffix("_temp")
    if "_" in compact:
        # HRIPCB variations use a board prefix followed by defect/sample suffixes.
        return compact.split("_")[0]
    digits = "".join(character for character in compact if character.isdigit())
    return digits[:5] if len(digits) == 8 else compact


def assert_no_group_leakage(items: Iterable[tuple[str, str]]) -> None:
    seen: dict[str, str] = {}
    for group, split in items:
        previous = seen.setdefault(group, split)
        if previous != split:
            raise ValueError(f"Group {group!r} appears in both {previous!r} and {split!r}")
