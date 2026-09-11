from __future__ import annotations

from dataclasses import dataclass

import cv2
import numpy as np


@dataclass(frozen=True)
class PreprocessConfig:
    clahe_clip_limit: float = 2.0
    clahe_grid_size: int = 8
    gaussian_kernel: int = 3

    def validate(self) -> None:
        if self.clahe_clip_limit <= 0 or self.clahe_grid_size < 1:
            raise ValueError("CLAHE settings must be positive")
        if self.gaussian_kernel < 1 or self.gaussian_kernel % 2 == 0:
            raise ValueError("gaussian_kernel must be a positive odd integer")


def validate_image(image: np.ndarray, name: str = "image") -> None:
    if not isinstance(image, np.ndarray) or image.size == 0:
        raise ValueError(f"{name} must be a non-empty NumPy array")
    if image.ndim not in (2, 3):
        raise ValueError(f"{name} must have 2 or 3 dimensions")
    if image.ndim == 3 and image.shape[2] not in (1, 3, 4):
        raise ValueError(f"{name} has an unsupported channel count: {image.shape[2]}")
    if image.shape[0] < 16 or image.shape[1] < 16:
        raise ValueError(f"{name} is too small for registration: {image.shape[:2]}")
    if image.dtype not in (np.uint8, np.uint16, np.float32, np.float64):
        raise ValueError(f"{name} has unsupported dtype: {image.dtype}")
    if not np.isfinite(image).all():
        raise ValueError(f"{name} contains NaN or infinite values")


def to_uint8(image: np.ndarray) -> np.ndarray:
    validate_image(image)
    if image.dtype == np.uint8:
        return image.copy()
    if image.dtype == np.uint16:
        return cv2.convertScaleAbs(image, alpha=255.0 / 65535.0)
    minimum, maximum = float(image.min()), float(image.max())
    if maximum <= minimum:
        return np.zeros(image.shape, dtype=np.uint8)
    return np.clip((image - minimum) * 255.0 / (maximum - minimum), 0, 255).astype(np.uint8)


def to_grayscale(image: np.ndarray) -> np.ndarray:
    converted = to_uint8(image)
    if converted.ndim == 2:
        return converted
    if converted.shape[2] == 1:
        return converted[:, :, 0]
    code = cv2.COLOR_BGRA2GRAY if converted.shape[2] == 4 else cv2.COLOR_BGR2GRAY
    return cv2.cvtColor(converted, code)


def preprocess_for_features(image: np.ndarray, config: PreprocessConfig | None = None) -> np.ndarray:
    config = config or PreprocessConfig()
    config.validate()
    gray = to_grayscale(image)
    if config.gaussian_kernel > 1:
        gray = cv2.GaussianBlur(gray, (config.gaussian_kernel, config.gaussian_kernel), 0)
    clahe = cv2.createCLAHE(
        clipLimit=config.clahe_clip_limit,
        tileGridSize=(config.clahe_grid_size, config.clahe_grid_size),
    )
    return clahe.apply(gray)
