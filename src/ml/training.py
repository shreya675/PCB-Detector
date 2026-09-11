from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any

from .config import YoloExperimentConfig
from .metadata import append_registry, build_run_metadata, write_json
from .metrics import extract_numeric_metrics
from .preflight import validate_yolo_dataset
from .reproducibility import seed_everything


def _default_model_factory(model_name: str):
    try:
        from ultralytics import YOLO
    except ImportError as exc:
        raise RuntimeError("Ultralytics is not installed. Run: pip install -e '.[ml]'") from exc
    return YOLO(model_name)


def _device(value: str) -> str | int:
    return value if value != "auto" else ""


def train_baseline(config: YoloExperimentConfig, model_factory: Callable[[str], Any] | None = None) -> dict[str, Any]:
    config.validate()
    dataset = validate_yolo_dataset(Path(config.data))
    seed_everything(config.seed, config.deterministic)
    factory = model_factory or _default_model_factory
    model = factory(config.model)
    results = model.train(
        data=str(Path(config.data).resolve()), epochs=config.epochs, imgsz=config.image_size,
        batch=config.batch, workers=config.workers, device=_device(config.device), seed=config.seed,
        deterministic=config.deterministic, patience=config.patience, project=config.project,
        name=config.name, exist_ok=False, plots=True, save=True, verbose=True,
    )
    observed = extract_numeric_metrics(results)
    save_dir = Path(getattr(results, "save_dir", Path(config.project) / config.name))
    weights = save_dir / "weights" / "best.pt"
    metadata = build_run_metadata(
        mode="train", config=config.as_dict(),
        dataset={"yaml": str(dataset.dataset_yaml), "split_counts": dataset.split_counts},
        metrics=observed, weights=weights if weights.is_file() else None,
    )
    write_json(save_dir / "run_metadata.json", metadata)
    append_registry(Path("models/registry.jsonl"), metadata)
    return metadata


def evaluate_model(weights: Path, config: YoloExperimentConfig,
                   model_factory: Callable[[str], Any] | None = None) -> dict[str, Any]:
    config.validate()
    if not weights.is_file():
        raise ValueError(f"Weights not found: {weights}")
    dataset = validate_yolo_dataset(Path(config.data), require_test=config.evaluation_split == "test")
    seed_everything(config.seed, config.deterministic)
    factory = model_factory or _default_model_factory
    model = factory(str(weights))
    results = model.val(
        data=str(Path(config.data).resolve()), imgsz=config.image_size, batch=config.batch,
        device=_device(config.device), conf=config.confidence, iou=config.iou,
        project=config.project, name=f"{config.name}-evaluation", plots=True, save_json=True,
        split=config.evaluation_split,
    )
    observed = extract_numeric_metrics(results)
    save_dir = Path(getattr(results, "save_dir", Path(config.project) / f"{config.name}-evaluation"))
    output = save_dir / "metrics.json"
    metadata = build_run_metadata(
        mode="evaluation", config=config.as_dict(),
        dataset={"yaml": str(dataset.dataset_yaml), "split_counts": dataset.split_counts,
                 "evaluated_split": config.evaluation_split},
        metrics=observed, weights=weights,
    )
    write_json(output, metadata)
    return metadata
