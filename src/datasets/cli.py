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
        command.add_argument("--val-fraction", type=float, default=0.1,
                             help="Share of board groups assigned to validation (test share stays 0.1)")
        command.add_argument("--official-split", type=Path, default=None, metavar="PCBDATA_DIR",
                             help="DeepPCB only: directory holding upstream trainval.txt and test.txt; "
                                  "uses the paper's 1000/500 protocol instead of the grouped split")
    validate = subparsers.add_parser("validate", help="Validate a prepared dataset manifest")
    validate.add_argument("--dataset", type=Path, required=True)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    if args.command == "deeppcb":
        records = prepare_deeppcb(args.source, args.output, args.val_fraction, args.official_split)
        print(f"Prepared {len(records)} DeepPCB images at {args.output}")
    elif args.command == "hripcb":
        records = prepare_hripcb(args.source, args.output)
        print(f"Prepared {len(records)} HRIPCB images at {args.output}")
    else:
        stats = validate_prepared_dataset(args.dataset)
        print(f"Validated {stats['images']} images and {stats['annotations']} annotations")


if __name__ == "__main__":
    main()
