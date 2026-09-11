from __future__ import annotations

import argparse
import json
from pathlib import Path

from .config import load_experiment_config
from .inference import predict_images
from .preflight import validate_yolo_dataset
from .training import evaluate_model, train_baseline


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(description="PCB AOI YOLO baseline")
    commands = root.add_subparsers(dest="command", required=True)
    for name in ("preflight", "train"):
        command = commands.add_parser(name)
        command.add_argument("--config", type=Path, default=Path("ml/configs/yolo_baseline.yaml"))
    evaluate = commands.add_parser("evaluate")
    evaluate.add_argument("--config", type=Path, default=Path("ml/configs/yolo_baseline.yaml"))
    evaluate.add_argument("--weights", type=Path, required=True)
    predict = commands.add_parser("predict")
    predict.add_argument("--weights", type=Path, required=True)
    predict.add_argument("--source", type=Path, nargs="+", required=True)
    predict.add_argument("--output", type=Path, default=Path("reports/predictions"))
    predict.add_argument("--confidence", type=float, default=0.25)
    predict.add_argument("--iou", type=float, default=0.50)
    return root


def main() -> None:
    args = parser().parse_args()
    if args.command == "predict":
        predictions = predict_images(args.weights, args.source, args.output, args.confidence, args.iou)
        print(f"Saved {len(predictions)} predictions to {args.output}")
        return
    config = load_experiment_config(args.config)
    if args.command == "preflight":
        report = validate_yolo_dataset(Path(config.data))
        print(json.dumps({"dataset": str(report.dataset_yaml), "splits": report.split_counts,
                          "classes": report.class_names}, indent=2))
    elif args.command == "train":
        metadata = train_baseline(config)
        print(json.dumps(metadata, indent=2))
    else:
        metadata = evaluate_model(args.weights, config)
        print(json.dumps(metadata, indent=2))


if __name__ == "__main__":
    main()
