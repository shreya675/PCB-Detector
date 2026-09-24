"""Template-based defect classification for DeepPCB-style aligned image pairs.

Copper is dark (black) on a light background.  Given a candidate box on the test
image and the defect-free template, decide the defect type from how the copper
changed inside the box:

    copper added,   traces merged            -> short_circuit
    copper added,   attached to a trace      -> spur
    copper added,   floating                 -> spurious_copper
    copper removed, trace broken             -> open_circuit
    copper removed, hole enclosed in copper  -> pin_hole
    copper removed, notch on a trace edge    -> mouse_bite
    nothing changed                          -> None (not a defect)
"""
from __future__ import annotations

import numpy as np
from PIL import Image

CLASS_NAMES = ["open_circuit", "short_circuit", "spur", "spurious_copper", "mouse_bite", "missing_hole", "pin_hole"]


def load_copper_mask(path) -> np.ndarray:
    return np.array(Image.open(path).convert("L")) < 128


def _components(mask: np.ndarray, min_size: int) -> int:
    from scipy import ndimage

    labels, count = ndimage.label(mask)
    if count == 0:
        return 0
    sizes = np.asarray(ndimage.sum(np.ones_like(mask, dtype=int), labels, range(1, count + 1)))
    return int((sizes >= min_size).sum())


def _crop(mask: np.ndarray, box, margin: int) -> np.ndarray:
    h, w = mask.shape
    x1 = max(0, int(box[0]) - margin); y1 = max(0, int(box[1]) - margin)
    x2 = min(w, int(box[2]) + margin); y2 = min(h, int(box[3]) + margin)
    return mask[y1:y2, x1:x2]


def classify_region(test_mask: np.ndarray, template_mask: np.ndarray, box, margin: int = 4,
                    connectivity_margin: int = 6, min_change: int = 4,
                    min_component: int = 60) -> tuple[str | None, dict]:
    from scipy import ndimage  # optional dependency, only needed for template rules

    X = _crop(test_mask, box, margin)
    T = _crop(template_mask, box, margin)
    if X.size == 0:
        return None, {}
    # ignore 1-px alignment noise at copper edges
    added = X & ~ndimage.binary_dilation(T, iterations=1)
    removed = T & ~ndimage.binary_dilation(X, iterations=1)
    n_added, n_removed = int(added.sum()), int(removed.sum())
    info = {"added": n_added, "removed": n_removed}
    if max(n_added, n_removed) < min_change:
        return None, info
    n_t = _components(_crop(template_mask, box, connectivity_margin), min_component)
    n_x = _components(_crop(test_mask, box, connectivity_margin), min_component)
    info.update({"components_template": n_t, "components_test": n_x})
    if n_added >= n_removed:
        touches = bool((ndimage.binary_dilation(added, iterations=2) & T).any())
        if n_x < n_t:
            return "short_circuit", info
        if touches:
            return "spur", info
        return "spurious_copper", info
    # copper removed
    if n_x > n_t:
        return "open_circuit", info
    # enclosed hole: the removed area does not touch template background
    background = ~ndimage.binary_dilation(T, iterations=1)
    enclosed = not bool((ndimage.binary_dilation(removed, iterations=2) & background).any())
    if enclosed:
        return "pin_hole", info
    return "mouse_bite", info


# Where the template rule is more reliable than the detector, its verdict wins.
RULE_WINS = {"short_circuit", "spurious_copper", "open_circuit", "pin_hole"}
ADDED_FAMILY = {"short_circuit", "spur", "spurious_copper"}
REMOVED_FAMILY = {"open_circuit", "mouse_bite", "pin_hole", "missing_hole"}


def combine(model_class: str, rule_class: str | None) -> str | None:
    """Merge the detector's class with the template rule's class.

    Returns None when the region is unchanged versus the template (not a defect).
    """
    if rule_class is None:
        return None
    if rule_class in RULE_WINS:
        return rule_class
    same_family = (model_class in ADDED_FAMILY) == (rule_class in ADDED_FAMILY)
    if not same_family:
        return rule_class
    if rule_class == "spur" and model_class == "short_circuit":
        return "spur"
    return model_class


def agnostic_nms(detections, iou_threshold: float = 0.2):
    """Keep one box per physical defect regardless of class. detections: (cls, score, box)."""
    kept = []
    for det in sorted(detections, key=lambda d: -d[1]):
        if all(_iou(det[2], k[2]) < iou_threshold for k in kept):
            kept.append(det)
    return kept


def _iou(a, b) -> float:
    ix1, iy1 = max(a[0], b[0]), max(a[1], b[1])
    ix2, iy2 = min(a[2], b[2]), min(a[3], b[3])
    inter = max(0.0, ix2 - ix1) * max(0.0, iy2 - iy1)
    union = (a[2] - a[0]) * (a[3] - a[1]) + (b[2] - b[0]) * (b[3] - b[1]) - inter
    return inter / union if union > 0 else 0.0


def scale_box(box, factor: float = 1.15):
    cx, cy = (box[0] + box[2]) / 2, (box[1] + box[3]) / 2
    w, h = (box[2] - box[0]) * factor, (box[3] - box[1]) * factor
    return (cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2)


def postprocess(detections, test_mask=None, template_mask=None, *, nms_iou: float = 0.2,
                box_scale: float = 1.15, relabel: bool = False):
    """Full post-processing chain.

    detections: iterable of (class_name, score, (x1, y1, x2, y2)) in test-image coordinates.
    When a template mask is supplied, detections whose region is identical to the reference
    are dropped.  With ``relabel=True`` the template rules may also override the detector's
    class; this helped on one held-out board but hurt on the official DeepPCB test split, so
    it is off by default.
    Returns a list of (class_name, score, box).
    """
    refined = []
    for class_name, score, box in detections:
        if template_mask is not None and test_mask is not None:
            rule, _ = classify_region(test_mask, template_mask, box)
            if rule is None:
                continue  # unchanged versus the reference: not a defect
            if relabel:
                class_name = combine(class_name, rule) or class_name
        refined.append((class_name, score, scale_box(box, box_scale)))
    return agnostic_nms(refined, nms_iou)
