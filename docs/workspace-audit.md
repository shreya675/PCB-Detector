# Workspace audit and corrections

The active project is `pcb-aoi-final/pcb-aoi`. All nine earlier phase directories
were inventoried and compared by file path and SHA-256. No earlier file path is
missing from the final project. `workspace-inventory.json` records the inventory
before corrections. Historical snapshots were subsequently removed during GitHub preparation after verifying their hashes were unchanged.

## Dataset and model preparation

- Preserve DeepPCB `pin_hole` separately from HRIPCB `missing_hole`. The original
  converter mislabeled these as the same defect. Regenerate previously converted
  data before training. The taxonomy includes both, but a category without
  training examples is not an evaluated capability.
- Discover DeepPCB labels in the official sibling `<board>_not` directories;
  accept whitespace and comma annotation formats.
- Reject duplicate IDs and ambiguous HRIPCB image filenames. Group HRIPCB
  variants by board prefix instead of combining board and sample digits.
- Check normalized YOLO boxes for valid classes, finite values, and image bounds.
- Resolve checkpoint class names from metadata instead of assuming class order.
  Generic COCO checkpoints fail explicitly.
- Evaluate on the configured held-out split (default `test`) and save metrics
  alongside the actual Ultralytics run, including auto-incremented directories.

Sources: [DeepPCB annotation specification](https://github.com/tangsanli5201/DeepPCB#image-annotation)
and [official file layout](https://github.com/tangsanli5201/DeepPCB/blob/master/PCBData/trainval.txt).
No external application implementation was copied.

## CV and inspection

- Run YOLO on the aligned image so learned and reference boxes share coordinates.
- Exclude components at unobserved alignment borders. Partial reference coverage
  returns a review warning even when no defect is detected.
- Record whether reference analysis actually ran and which coordinate frame is used.
- Make skeleton erosion terminate for an all-foreground mask.
- Reject tiny/corrupt uploads as validation errors.
- Keep contour components and trace findings explicitly marked as heuristics.

CLAHE is used for feature registration. Detector input stays in BGR, consistent
with the existing training path; preprocessing is not silently substituted at
inference. A separately trained component adapter exists, but the HTTP inspection
path currently uses contour candidates. Advanced assembly defect models remain
future work.

## API, dashboard, reports, deployment

- Add workflow tests covering inspection submission, persistence, history, image
  retrieval, PDF retrieval, and missing weights without fabricated PASS results.
- Serialize SQLite timestamps explicitly as UTC.
- Fix the TypeScript build configuration and local Vite API proxy.
- Add history loading controls, visible refresh failures, and accurate analytics
  scope labels. Analytics cover loaded records rather than claiming global counts.
- Include partial-coverage warnings in the PDF and fit images within cell padding.
- Install ML dependencies in the API image by default; support `INSTALL_ML=false`
  for a lighter API-only image. Accept two 20 MB uploads through Nginx.
- Use the frontend dependency lockfile and exclude generated artifacts.
- Add Windows setup instructions and correct premature completion claims.

## Remaining work requiring real artifacts

Acquire and prepare licensed public datasets; train real weights; evaluate on
held-out boards; review false positives/negatives; record hardware and latency.
The model-performance page currently explains the missing evaluation and does
not load metric artifacts. Docker runtime and PostgreSQL integration require a
running Docker engine. This remains an academic/research prototype.

## Validation

Validation results are appended after the final checks. Test doubles and synthetic
fixtures exercise software behavior only, not PCB detection accuracy.

### Verified results

- Full Pytest suite: **109 passed, 0 failed, 0 skipped**. Two upstream test-client deprecation warnings remain.
- Ruff lint and Python compilation: passed.
- React TypeScript check and Vite production build: passed.
- SQLite Alembic migration: reached `0001_initial_schema (head)`.
- Docker Compose configuration: valid. Container build/runtime and PostgreSQL checks were not run because Docker's engine was unavailable.
- PDF QA: two-page synthetic fixture rendered with Poppler and visually reviewed; long-report pagination is covered by tests.
- After replacing the PDF coordinate arrow with plain text, the PDF tests and lint were rerun.

The Windows PDF test failures were fixed by closing document handles before temporary-directory cleanup.
The verifier now runs the full suite once and writes observed results to `reports/validation-summary.json`.

See [complete file change list](changes.md). Both trained weights and real evaluation results remain absent; no model accuracy is claimed.
