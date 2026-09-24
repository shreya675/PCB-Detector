from __future__ import annotations

import json
from pathlib import Path

from fastapi import APIRouter

from backend.app.core.config import settings
from src.ml.metadata import sha256_file

router = APIRouter(prefix="/api", tags=["model"])


def load_model_card(path: Path) -> dict | None:
    if not path.is_file():
        return None
    try:
        card = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return card if isinstance(card, dict) else None


@router.get("/model")
def model_info() -> dict:
    weights = Path(settings.model_path)
    available = weights.is_file()
    version = f"sha256:{sha256_file(weights)[:12]}" if available else "unavailable"
    card = load_model_card(Path(settings.model_card_path))
    # Only show evaluation numbers that belong to the weights actually loaded.
    card_matches = bool(card and card.get("weights", {}).get("sha256", "").startswith(version.removeprefix("sha256:")))
    return {
        "model_status": "available" if available else "missing",
        "weights_file": weights.name,
        "model_version": version,
        "confidence_threshold": settings.confidence_threshold,
        "postprocess": {
            "enabled": settings.enable_postprocess,
            "nms_iou": settings.postprocess_nms_iou,
            "box_scale": settings.postprocess_box_scale,
        },
        "evaluation": card if card_matches else None,
        "evaluation_mismatch": bool(card) and available and not card_matches,
    }
