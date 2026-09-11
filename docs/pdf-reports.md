# Phase 9 — PDF inspection reports

Every successful persisted inspection generates a paginated PDF beside its image artifacts. Existing records without a report are generated lazily when the report endpoint is requested.

## Contents

- Inspection ID, timestamp, and PASS/WARNING/FAIL status
- Critical, major, minor, and total finding counts
- Annotated PCB image with aspect-ratio preservation
- Repeating defect-table headers across pages
- Defect type, severity, confidence/heuristic label, bounding box, and source
- Reference registration quality when available
- Model version and interpretation policy
- Page numbers and prototype disclaimer on every page

## Integrity policy

The report reads stored inspection data; it does not recompute or invent metrics. A `null` confidence renders as `Heuristic`. Missing annotated images and unsupported statuses fail explicitly. Partial PDFs are removed after generation errors.

## API

`GET /api/inspections/{id}/report` generates a missing report on demand and returns it as `application/pdf`.

## Limitations

The PDF is an academic/research record, not an industrial certificate, electrical test, or replacement for qualified review. Production deployments should add signing, immutable object storage, access controls, retention, audit trails, and validated report templates.
