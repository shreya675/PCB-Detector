from __future__ import annotations

import re
from pathlib import Path
from uuid import UUID

import cv2
import numpy as np

from src.cv.io import save_image
from src.cv.preprocessing import validate_image


class InvalidUploadError(ValueError):
    pass


class InspectionStorage:
    def __init__(self, root: Path, max_upload_mb: int = 20):
        self.root = root
        self.max_bytes = max_upload_mb * 1024 * 1024

    def inspection_dir(self, inspection_id: UUID | str) -> Path:
        path = self.root / str(inspection_id)
        path.mkdir(parents=True, exist_ok=True)
        return path

    def decode_upload(self, content: bytes, filename: str | None, role: str) -> tuple[np.ndarray, Path]:
        if not content:
            raise InvalidUploadError(f"{role} image is empty")
        if len(content) > self.max_bytes:
            raise InvalidUploadError(f"{role} image exceeds {self.max_bytes // (1024 * 1024)} MB")
        try:
            image = cv2.imdecode(np.frombuffer(content, dtype=np.uint8), cv2.IMREAD_COLOR)
        except cv2.error as exc:
            raise InvalidUploadError(f"{role} image is corrupt or unsupported") from exc
        if image is None or image.size == 0:
            raise InvalidUploadError(f"{role} image is corrupt or unsupported")
        try:
            validate_image(image, role)
        except ValueError as exc:
            raise InvalidUploadError(str(exc)) from exc
        safe = re.sub(r"[^A-Za-z0-9._-]+", "_", filename or f"{role}.png")
        suffix = Path(safe).suffix.lower()
        if suffix not in {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff"}:
            suffix = ".png"
        return image, Path(f"{role}{suffix}")

    def save_input(self, inspection_id: UUID | str, relative: Path, image: np.ndarray) -> Path:
        destination = self.inspection_dir(inspection_id) / relative
        save_image(destination, image)
        return destination

    def save_annotated(self, inspection_id: UUID | str, image: np.ndarray) -> Path:
        destination = self.inspection_dir(inspection_id) / "annotated.png"
        save_image(destination, image)
        return destination
