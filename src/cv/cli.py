from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path

from .alignment import AlignmentConfig, align_to_reference
from .difference import DifferenceConfig, compute_difference
from .io import load_image, save_image
from .visualization import draw_difference_regions


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Align a test PCB to a reference PCB")
    parser.add_argument("--reference", type=Path, required=True)
    parser.add_argument("--test", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=Path("reports/alignment"))
    parser.add_argument("--min-matches", type=int, default=12)
    parser.add_argument("--difference-threshold", type=int)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    reference, test = load_image(args.reference), load_image(args.test)
    alignment = align_to_reference(reference, test, AlignmentConfig(min_matches=args.min_matches))
    args.output.mkdir(parents=True, exist_ok=True)
    report = {"reference": str(args.reference), "test": str(args.test),
              "alignment": alignment.quality_dict(), "differences": None}
    if alignment.aligned_image is not None:
        save_image(args.output / "aligned.png", alignment.aligned_image)
        save_image(args.output / "valid_mask.png", alignment.valid_mask)
    if alignment.success:
        differences = compute_difference(
            reference, alignment.aligned_image, alignment.valid_mask,
            DifferenceConfig(threshold=args.difference_threshold),
        )
        save_image(args.output / "difference.png", differences.absolute_difference)
        save_image(args.output / "difference_mask.png", differences.binary_mask)
        save_image(args.output / "differences_annotated.png",
                   draw_difference_regions(alignment.aligned_image, differences.regions))
        report["differences"] = {
            "changed_pixel_ratio": differences.changed_pixel_ratio,
            "regions": [asdict(region) for region in differences.regions],
        }
    (args.output / "registration.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    if not alignment.success:
        raise SystemExit(f"Registration failed: {alignment.reason}")
    print(f"Registration passed; outputs saved to {args.output}")


if __name__ == "__main__":
    main()
