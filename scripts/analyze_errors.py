"""Error analysis for a YOLO evaluation run.

Reads the ``predictions.json`` that Ultralytics writes during ``evaluate`` and the
ground-truth YOLO labels of the evaluated split, matches them, and reports what the
false positives and false negatives actually are.  Writes contact sheets so the
mistakes can be inspected visually.

Usage (from the project root):
    python scripts/analyze_errors.py --predictions <run>/predictions.json \
        --dataset data/processed/deeppcb --split test --conf 0.25 --output reports/error-analysis
"""
from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path

from PIL import Image, ImageDraw

CLASS_NAMES = ["open_circuit", "short_circuit", "spur", "spurious_copper", "mouse_bite", "missing_hole", "pin_hole"]
IMAGE_SUFFIXES = (".jpg", ".jpeg", ".png", ".bmp")


def iou(a: tuple[float, float, float, float], b: tuple[float, float, float, float]) -> float:
    ix1, iy1 = max(a[0], b[0]), max(a[1], b[1])
    ix2, iy2 = min(a[2], b[2]), min(a[3], b[3])
    inter = max(0.0, ix2 - ix1) * max(0.0, iy2 - iy1)
    union = (a[2] - a[0]) * (a[3] - a[1]) + (b[2] - b[0]) * (b[3] - b[1]) - inter
    return inter / union if union > 0 else 0.0


def load_ground_truth(dataset: Path, split: str) -> dict[str, tuple[Path, list[tuple[int, tuple]]]]:
    records: dict[str, tuple[Path, list]] = {}
    for image_path in sorted((dataset / "images" / split).iterdir()):
        if image_path.suffix.lower() not in IMAGE_SUFFIXES:
            continue
        label_path = dataset / "labels" / split / f"{image_path.stem}.txt"
        with Image.open(image_path) as image:
            width, height = image.size
        boxes = []
        if label_path.is_file():
            for line in label_path.read_text().splitlines():
                parts = line.split()
                if len(parts) < 5:
                    continue
                cls, cx, cy, w, h = int(parts[0]), *map(float, parts[1:5])
                boxes.append((cls, (cx * width - w * width / 2, cy * height - h * height / 2,
                                    cx * width + w * width / 2, cy * height + h * height / 2)))
        records[image_path.stem] = (image_path, boxes)
    return records


def load_predictions(path: Path, conf: float, class_count: int) -> dict[str, list[tuple[int, float, tuple]]]:
    raw = json.loads(path.read_text())
    max_category = max((int(item["category_id"]) for item in raw), default=0)
    one_based = max_category >= class_count  # Ultralytics may write 1-based ids for custom datasets
    predictions: dict[str, list] = defaultdict(list)
    for item in raw:
        if float(item["score"]) < conf:
            continue
        cls = int(item["category_id"]) - (1 if one_based else 0)
        x, y, w, h = item["bbox"]
        predictions[str(item["image_id"])].append((cls, float(item["score"]), (x, y, x + w, y + h)))
    return predictions


def match(gt_boxes, predictions, iou_threshold: float = 0.5):
    """Greedy matching by descending confidence. Returns (tp, fp_with_reason, fn)."""
    used = set()
    tp, fp = [], []
    for cls, score, box in sorted(predictions, key=lambda p: -p[1]):
        best_iou, best_index = 0.0, -1
        for index, (gt_cls, gt_box) in enumerate(gt_boxes):
            if index in used or gt_cls != cls:
                continue
            overlap = iou(box, gt_box)
            if overlap > best_iou:
                best_iou, best_index = overlap, index
        if best_iou >= iou_threshold:
            used.add(best_index)
            tp.append((cls, score, box))
            continue
        # Classify the false positive.
        reason = "background"
        overlaps_same_class = any(gt_cls == cls and iou(box, gt_box) >= iou_threshold for gt_cls, gt_box in gt_boxes)
        other = [(gt_cls, iou(box, gt_box)) for gt_cls, gt_box in gt_boxes if gt_cls != cls]
        if overlaps_same_class:
            reason = "duplicate"
        elif other and max(o[1] for o in other) >= iou_threshold:
            wrong = max(other, key=lambda o: o[1])[0]
            reason = f"misclassified (actually {CLASS_NAMES[wrong]})"
        elif any(iou(box, gt_box) > 0.1 for _, gt_box in gt_boxes):
            reason = "poor localisation"
        fp.append((cls, score, box, reason))
    fn = [(gt_cls, gt_box) for index, (gt_cls, gt_box) in enumerate(gt_boxes) if index not in used]
    return tp, fp, fn


def template_differs(test_path: Path, reference_path: Path, box, threshold: float, margin: int = 6) -> bool:
    """True when the boxed region of the test image differs from the defect-free template."""
    with Image.open(test_path) as test, Image.open(reference_path) as reference:
        test = test.convert("L")
        reference = reference.convert("L").resize(test.size)
        x1, y1 = max(0, int(box[0]) - margin), max(0, int(box[1]) - margin)
        x2, y2 = min(test.width, int(box[2]) + margin), min(test.height, int(box[3]) + margin)
        if x2 <= x1 or y2 <= y1:
            return True
        a = list(test.crop((x1, y1, x2, y2)).tobytes())
        b = list(reference.crop((x1, y1, x2, y2)).tobytes())
    differing = sum(1 for p, q in zip(a, b) if abs(p - q) > 96)
    return differing / max(1, len(a)) >= threshold


def match_any_class(gt_boxes, predictions, iou_threshold: float = 0.3):
    """Defect-level matching: a prediction counts if it lands on any labelled defect."""
    used = set()
    tp = fp = 0
    for cls, score, box in sorted(predictions, key=lambda p: -p[1]):
        best_iou, best_index = 0.0, -1
        for index, (_, gt_box) in enumerate(gt_boxes):
            if index in used:
                continue
            overlap = iou(box, gt_box)
            if overlap > best_iou:
                best_iou, best_index = overlap, index
        if best_iou >= iou_threshold:
            used.add(best_index)
            tp += 1
        else:
            fp += 1
    return tp, fp, len(gt_boxes) - len(used)


def contact_sheet(items, output: Path, title: str, crop: int = 96, columns: int = 8) -> None:
    if not items:
        return
    tile = crop * 2
    rows = (len(items) + columns - 1) // columns
    sheet = Image.new("RGB", (columns * tile, rows * (tile + 28)), "white")
    draw = ImageDraw.Draw(sheet)
    for index, (image_path, box, label, colour) in enumerate(items):
        with Image.open(image_path) as image:
            image = image.convert("RGB")
            cx, cy = (box[0] + box[2]) / 2, (box[1] + box[3]) / 2
            region = image.crop((int(cx - crop), int(cy - crop), int(cx + crop), int(cy + crop)))
            region_draw = ImageDraw.Draw(region)
            region_draw.rectangle((box[0] - cx + crop, box[1] - cy + crop, box[2] - cx + crop, box[3] - cy + crop),
                                  outline=colour, width=2)
        x, y = (index % columns) * tile, (index // columns) * (tile + 28)
        sheet.paste(region, (x, y))
        draw.text((x + 4, y + tile + 4), label[:34], fill="black")
        draw.text((x + 4, y + tile + 15), image_path.stem, fill="gray")
    sheet.save(output)
    print(f"{title}: {len(items)} crops -> {output}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--predictions", type=Path, required=True)
    parser.add_argument("--dataset", type=Path, default=Path("data/processed/deeppcb"))
    parser.add_argument("--split", default="test")
    parser.add_argument("--conf", type=float, default=0.25)
    parser.add_argument("--iou", type=float, default=0.5)
    parser.add_argument("--output", type=Path, default=Path("reports/error-analysis"))
    parser.add_argument("--exclude", nargs="*", default=[], help="Image stems to leave out (e.g. corrupted samples)")
    parser.add_argument("--postprocess", action="store_true",
                        help="Apply src.inspection.template_rules.postprocess (agnostic NMS, box scale, "
                             "and template-based class refinement when references exist)")
    parser.add_argument("--relabel", action="store_true",
                        help="With --postprocess: also let template rules override the detector's class")
    parser.add_argument("--sweep", action="store_true", help="Per-class threshold sweep: lowest confidence reaching 95%% precision")
    parser.add_argument("--target-precision", type=float, default=0.95)
    parser.add_argument("--template-filter", type=float, default=None, metavar="FRACTION",
                        help="Drop predictions whose region is identical to the reference template "
                             "(keep if at least FRACTION of pixels differ, e.g. 0.02)")
    args = parser.parse_args()

    ground_truth = load_ground_truth(args.dataset, args.split)
    predictions = load_predictions(args.predictions, args.conf, len(CLASS_NAMES))
    args.output.mkdir(parents=True, exist_ok=True)

    for stem in args.exclude:
        ground_truth.pop(stem, None)
        print(f"Excluded {stem}")
    if args.postprocess:
        import sys as _sys
        _sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
        from src.inspection.template_rules import load_copper_mask, postprocess
        changed = 0
        for stem, (image_path, _) in ground_truth.items():
            reference = args.dataset / "references" / args.split / image_path.name
            masks = (load_copper_mask(image_path), load_copper_mask(reference)) if reference.is_file() else (None, None)
            before = predictions.get(stem, [])
            named = [(CLASS_NAMES[c], s, b) for c, s, b in before]
            after = [(CLASS_NAMES.index(n), s, b) for n, s, b in postprocess(named, *masks, relabel=args.relabel)]
            changed += len(before) - len(after)
            predictions[stem] = after
        print(f"Post-processing removed {changed} predictions (duplicates / unchanged regions)")

    dropped_by_template = 0
    if args.template_filter is not None:
        for stem, (image_path, _) in ground_truth.items():
            reference = args.dataset / "references" / args.split / image_path.name
            if not reference.is_file():
                continue
            kept = [p for p in predictions.get(stem, []) if template_differs(image_path, reference, p[2], args.template_filter)]
            dropped_by_template += len(predictions.get(stem, [])) - len(kept)
            predictions[stem] = kept
        print(f"Template filter removed {dropped_by_template} predictions identical to the reference board")

    totals = Counter()
    agnostic = Counter()
    fp_reasons = Counter()
    per_class = defaultdict(Counter)
    fp_items, fn_items = [], []
    for stem, (image_path, gt_boxes) in ground_truth.items():
        a_tp, a_fp, a_fn = match_any_class(gt_boxes, predictions.get(stem, []))
        agnostic["tp"] += a_tp
        agnostic["fp"] += a_fp
        agnostic["fn"] += a_fn
        tp, fp, fn = match(gt_boxes, predictions.get(stem, []), args.iou)
        totals["tp"] += len(tp)
        totals["fp"] += len(fp)
        totals["fn"] += len(fn)
        for cls, _, _ in tp:
            per_class[cls]["tp"] += 1
        for cls, score, box, reason in fp:
            per_class[cls]["fp"] += 1
            fp_reasons[reason.split(" (")[0]] += 1
            fp_items.append((image_path, box, f"{CLASS_NAMES[cls]} {score:.2f} {reason}", "red"))
        for cls, box in fn:
            per_class[cls]["fn"] += 1
            fn_items.append((image_path, box, f"missed {CLASS_NAMES[cls]}", "orange"))

    precision = totals["tp"] / max(1, totals["tp"] + totals["fp"])
    recall = totals["tp"] / max(1, totals["tp"] + totals["fn"])
    print(f"\nAt confidence >= {args.conf}, IoU >= {args.iou}:")
    print(f"  true positives  {totals['tp']}")
    print(f"  false positives {totals['fp']}   precision {precision:.3f}")
    print(f"  false negatives {totals['fn']}   recall    {recall:.3f}")
    a_precision = agnostic["tp"] / max(1, agnostic["tp"] + agnostic["fp"])
    a_recall = agnostic["tp"] / max(1, agnostic["tp"] + agnostic["fn"])
    print(f"\nDefect-level (any class, IoU >= 0.3): precision {a_precision:.3f}  recall {a_recall:.3f}"
          f"  (fp {agnostic['fp']}, fn {agnostic['fn']})")
    print("\nWhy the false positives happen:")
    for reason, count in fp_reasons.most_common():
        print(f"  {count:4d}  {reason}")
    print("\nPer class (tp / fp / fn -> precision, recall):")
    for cls, name in enumerate(CLASS_NAMES):
        c = per_class[cls]
        if not (c["tp"] or c["fp"] or c["fn"]):
            continue
        p = c["tp"] / max(1, c["tp"] + c["fp"])
        r = c["tp"] / max(1, c["tp"] + c["fn"])
        print(f"  {name:16s} {c['tp']:4d} / {c['fp']:3d} / {c['fn']:3d}  ->  P {p:.3f}  R {r:.3f}")

    if args.sweep:
        print(f"\nPer-class threshold sweep (lowest confidence reaching precision >= {args.target_precision}):")
        thresholds = [round(0.25 + 0.05 * i, 2) for i in range(15)]
        recommended = {}
        for cls, name in enumerate(CLASS_NAMES):
            rows = []
            for threshold in thresholds:
                tp = fp = fn = 0
                for stem, (_, gt_boxes) in ground_truth.items():
                    class_gt = [(c, b) for c, b in gt_boxes if c == cls]
                    class_pred = [p for p in predictions.get(stem, []) if p[0] == cls and p[1] >= threshold]
                    t, f, n = match(class_gt, class_pred, args.iou)
                    tp += len(t); fp += len(f); fn += len(n)
                if tp + fn == 0:
                    break
                rows.append((threshold, tp / max(1, tp + fp), tp / max(1, tp + fn)))
            if not rows:
                continue
            hit = next((r for r in rows if r[1] >= args.target_precision), None)
            base = rows[0]
            if hit:
                recommended[name] = hit[0]
                print(f"  {name:16s} at {base[0]:.2f}: P {base[1]:.3f} R {base[2]:.3f}  ->  at {hit[0]:.2f}: P {hit[1]:.3f} R {hit[2]:.3f}")
            else:
                best = max(rows, key=lambda r: r[1])
                print(f"  {name:16s} at {base[0]:.2f}: P {base[1]:.3f} R {base[2]:.3f}  ->  never reaches target; best P {best[1]:.3f} at {best[0]:.2f} (R {best[2]:.3f})")
        (args.output / "recommended_thresholds.json").write_text(json.dumps(recommended, indent=2))

    contact_sheet(sorted(fp_items, key=lambda i: i[2]), args.output / "false_positives.png", "False positives")
    contact_sheet(fn_items, args.output / "false_negatives.png", "False negatives")
    summary = {"conf": args.conf, "iou": args.iou, "totals": dict(totals), "precision": precision, "recall": recall,
               "defect_level": {"precision": a_precision, "recall": a_recall, **dict(agnostic)},
               "excluded": args.exclude, "template_filter": args.template_filter,
               "dropped_by_template": dropped_by_template,
               "fp_reasons": dict(fp_reasons),
               "per_class": {CLASS_NAMES[c]: dict(v) for c, v in per_class.items()}}
    (args.output / "summary.json").write_text(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
