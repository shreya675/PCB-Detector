# Next version: bare-PCB photo inspection

## Scope

Detect copper-pattern defects in sharp, top-down photographs of bare PCBs.
Reference images must show the same board design. Populated-board component,
solder, polarity, and electrical-function inspection are outside this milestone.
Unknown image conditions and failed registration should require review, not imply
that a board is defect-free. This remains a research prototype.

## Progress

- Step 1: checkpoint/evaluation snapshot tooling added; see docs/baselines for executed snapshots.
- Step 2: scope and acquisition/annotation rules defined in this document.
- Step 3: empty photo collection workspace prepared; real image collection is pending.
- Steps 4–5: annotation, review, grouping and split freezing are pending actual images.
- Steps 6–10: baseline evaluation on new validation images, controlled experiments,
  final evaluation, and dashboard integration follow reviewed data.

## Collection workspace

Place original photos in `data/raw/pcb_photos_v1/images/` and corresponding clean
reference photos in `data/raw/pcb_photos_v1/references/`. Never overwrite originals.
Use unique filenames and one metadata row per test image, with paths relative to
`data/raw/pcb_photos_v1`. Do not put files into processed train/val/test folders yet.
The raw data directory is deliberately ignored by Git.

`metadata.csv` columns:

- image_id: unique identifier, not a person's name.
- image_path: relative path to the original test image.
- board_design_id: design family; related variants should share a group.
- physical_board_id: individual board identifier.
- capture_session: lighting/camera session identifier.
- camera: capture device identifier or model.
- reference_id: matching reference identifier, blank when unavailable.
- reference_path: relative reference image path, blank when unavailable.
- source: provenance, dataset name or own capture.
- annotation_status: unreviewed, annotated, reviewed_defective, reviewed_clean, uncertain.
- notes: image quality, licensing/provenance details, or ambiguity.

Capture evenly lit, sharply focused images with visible traces and minimal glare.
Include independently verified clean boards as well as defective boards. Do not
infer ground truth from the existing detector's predictions. Ambiguous defects
remain uncertain until reviewed. Record synthetic sources separately from real
photographs. Do not invent defects or annotation rows to fill the workspace.

## Annotation contract

Use YOLO normalized bounding boxes and these existing IDs:

| ID | Class |
|---|---|
| 0 | open_circuit |
| 1 | short_circuit |
| 2 | spur |
| 3 | spurious_copper |
| 4 | mouse_bite |
| 5 | missing_hole |
| 6 | pin_hole |

Label all visible supported defects. Empty labels mean reviewed clean, not
unannotated. Pin holes and missing drilled holes are different categories.
Check duplicates, annotation overlays, truncated boxes, and missed defects.
Never remove difficult test examples merely because the model performs poorly.

## Split and evaluation contract

Assign approximately 70/15/15 percent to training/validation/test by design group,
subject to enough independent designs and class coverage. Keep reference pairs,
physical boards, sessions for the same design, crops, and augmentations together.
Resolve grouping before augmentation. Do not manufacture independent test samples
by splitting near-duplicate captures. If groups are too few, use grouped
cross-validation for development and acquire an external final test set.

Only validation informs model, confidence, preprocessing and loss selection.
Record frozen split manifests and dataset hashes. Existing repeatedly inspected
DeepPCB tests remain benchmark/development evidence, not a new external test.
Keep the official DeepPCB protocol separate from the unseen-design protocol.

Report per-class precision/recall, mAP50, mAP50–95, false detections per verified
clean board, defective-board false PASS rate, and CPU latency. Detector metrics
do not validate heuristic reference findings or severity rules. Evaluate those
separately. Keep the current backend model until a replacement is explicitly
validated under its actual deployment settings.

## Experiments after collection

Compare the unchanged baseline, added data, realistic augmentation, overlapping
tiles, mild contrast normalization, and reference assistance one change at a time.
Keep architecture, data split and compute budget fixed for paired comparisons.
Only then tune learning rate, optimizer and box/cls/dfl loss weights. No gain is
assumed in advance. Repeat promising settings with multiple seeds when feasible.
