# Architecture

## Module boundaries

- `ml/`: dataset configuration, training, evaluation, and model export.
- `src/cv/`: image validation, preprocessing, ORB registration, homography, and differencing.
- `src/inspection/`: defect normalization, component comparison, severity, and orchestration.
- `backend/`: FastAPI transport, persistence, report access, and service wiring.
- `frontend/`: React/Vite engineering dashboard.
- `data/`, `models/`, `reports/`: local/generated artifacts excluded from Git by default.

The computer-vision and inspection layers remain framework-independent so they can be unit-tested without an API or database.

## Registration contract

The registration layer transforms a test image into reference coordinates and emits explicit quality evidence. Downstream comparison must require `AlignmentResult.success`; failed or low-quality registration must not be interpreted as a PCB defect.

## Component comparison contract

Component comparison consumes only reference-coordinate images from a successful registration. Detector confidence remains optional because the classical contour baseline does not produce calibrated probabilities. Semantic component claims require separately trained and documented component weights.

## Trace evidence contract

Trace analysis consumes only successfully aligned images and emits visual candidates plus diagnostic masks. Candidate evidence strength is a bounded heuristic, never a calibrated model confidence or electrical continuity result.

## Backend transaction contract

The API refuses to report PASS when model weights are unavailable, validates all uploads before persistence, and commits each inspection with its defect rows in one database transaction. Reference-derived findings remain explicitly marked heuristic.

## Dashboard data contract

The browser derives every KPI and magnitude bar from API records. It accesses inspection media through bounded image kinds rather than exposing arbitrary filesystem paths, and it renders missing model metrics as unavailable rather than zero.

## Report contract

PDF reports are generated from persisted inspection records and stored beside inspection artifacts. Null confidence is rendered as Heuristic, table headers repeat across pages, and every page carries the research-prototype disclaimer.
