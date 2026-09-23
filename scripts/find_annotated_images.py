"""Find DeepPCB images that have annotation overlays baked in (green boxes / text).

Some upstream DeepPCB files are visualisation samples rather than clean data.  Those
contain saturated green pixels that never occur in the binarised board images.

Usage:  python scripts/find_annotated_images.py --dataset data/processed/deeppcb
"""
from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image

IMAGE_SUFFIXES = (".jpg", ".jpeg", ".png", ".bmp")


def green_pixel_count(path: Path) -> int:
    with Image.open(path) as image:
        rgb = image.convert("RGB")
        r, g, b = rgb.split()
        # saturated green: G high, R and B low
        mask = Image.eval(g, lambda v: 255 if v > 180 else 0)
        not_red = Image.eval(r, lambda v: 255 if v < 120 else 0)
        not_blue = Image.eval(b, lambda v: 255 if v < 120 else 0)
        from PIL import ImageChops
        combined = ImageChops.multiply(ImageChops.multiply(mask, not_red), not_blue)
        return combined.histogram()[255]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, default=Path("data/processed/deeppcb"))
    parser.add_argument("--min-pixels", type=int, default=50)
    args = parser.parse_args()
    suspicious = []
    for split_dir in sorted((args.dataset / "images").iterdir()):
        for image_path in sorted(split_dir.iterdir()):
            if image_path.suffix.lower() not in IMAGE_SUFFIXES:
                continue
            count = green_pixel_count(image_path)
            if count >= args.min_pixels:
                suspicious.append((split_dir.name, image_path.stem, count))
    if not suspicious:
        print("No images with annotation overlays found.")
        return
    print(f"{len(suspicious)} image(s) contain green overlay pixels:")
    for split, stem, count in suspicious:
        print(f"  {split:6s} {stem}  ({count} px)")
    print("\nExclude them with:  --exclude " + " ".join(stem for _, stem, _ in suspicious))


if __name__ == "__main__":
    main()
