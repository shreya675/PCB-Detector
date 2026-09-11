from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np


def load_image(path: Path, flags: int = cv2.IMREAD_COLOR) -> np.ndarray:
    if not path.is_file() or path.stat().st_size == 0:
        raise ValueError(f"Image is missing or empty: {path}")
    encoded = np.fromfile(path, dtype=np.uint8)
    image = cv2.imdecode(encoded, flags)
    if image is None or image.size == 0:
        raise ValueError(f"Image is corrupt or unsupported: {path}")
    return image


def save_image(path: Path, image: np.ndarray) -> None:
    if image is None or image.size == 0:
        raise ValueError("Cannot save an empty image")
    path.parent.mkdir(parents=True, exist_ok=True)
    suffix = path.suffix.lower() or ".png"
    ok, encoded = cv2.imencode(suffix, image)
    if not ok:
        raise ValueError(f"OpenCV could not encode image as {suffix}")
    encoded.tofile(path)
