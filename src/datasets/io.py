from __future__ import annotations

import hashlib
from pathlib import Path

import cv2
import numpy as np

IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff"}


def read_image_size(path: Path) -> tuple[int, int]:
    """Return (width, height) and reject missing, empty, or corrupt images."""
    if not path.is_file() or path.stat().st_size == 0:
        raise ValueError(f"Image is missing or empty: {path}")
    encoded = np.fromfile(path, dtype=np.uint8)
    image = cv2.imdecode(encoded, cv2.IMREAD_UNCHANGED)
    if image is None or image.size == 0:
        raise ValueError(f"Image is corrupt or unsupported: {path}")
    height, width = image.shape[:2]
    return int(width), int(height)


def sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(chunk_size):
            digest.update(chunk)
    return digest.hexdigest()
