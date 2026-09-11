from __future__ import annotations

import argparse
from pathlib import Path

from .prepare import prepare_deeppcb, prepare_hripcb, validate_prepared_dataset


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Prepare PCB datasets for Ultralytics YOLO")
    subparsers = parser.add_subparsers(dest="command", required=True)
    for name in ("deeppcb", "hripcb"):
        command = subparsers.add_parser(name, help=f"Convert {name.upper()} to canonical YOLO format")
        command.add_argument("--source", type=Path, required=True)
        command.add_argument("--output", type=Path, required=True)
    validate = subparsers.add_parser("validate", help="Validate a prepared dataset manifest")
    validate.add_argument("--dataset", type=Path, required=True)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    if args.command == "deeppcb":
        records = prepare_deeppcb(args.source, args.output)
        print(f"Prepared {len(records)} DeepPCB images at {args.output}")
    elif args.command == "hripcb":
        records = prepare_hripcb(args.source, args.output)
        print(f"Prepared {len(records)} HRIPCB images at {args.output}")
    else:
        stats = validate_prepared_dataset(args.dataset)
        print(f"Validated {stats['images']} images and {stats['annotations']} annotations")


if __name__ == "__main__":
    main()
