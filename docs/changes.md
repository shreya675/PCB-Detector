# Files changed during the audit

Active project: `pcb-aoi-final/pcb-aoi`. Redundant historical snapshots were subsequently removed during GitHub preparation.

## Added

- `C:/PCB detector/README.md` (workspace entry point)
- `docs/workspace-audit.md`
- `docs/workspace-inventory.json`
- `docs/changes.md`
- `frontend/package-lock.json`
- `frontend/.dockerignore`
- `src/ml/classes.py`
- `tests/test_checkpoint_classes.py`
- `tests/test_inspection_regressions.py`
- `tests/test_evaluation_regressions.py`
- `tests/test_api_workflow.py`

## Modified

- `.github/workflows/ci.yml`
- `.gitignore`
- `Dockerfile`
- `README.md`
- `backend/app/api/routes/health.py`
- `backend/app/api/routes/inspections.py`
- `backend/app/core/config.py`
- `backend/app/core/severity.yaml`
- `backend/app/db/models.py`
- `backend/app/schemas/inspections.py`
- `backend/app/services/detector.py`
- `backend/app/services/inspection_engine.py`
- `backend/app/services/pdf_report.py`
- `backend/app/services/severity.py`
- `backend/app/services/storage.py`
- `docs/datasets.md`
- `docs/deployment.md`
- `docs/model-classes.md`
- `docs/model-training.md`
- `docs/testing.md`
- `frontend/Dockerfile`
- `frontend/nginx.conf`
- `frontend/package.json`
- `frontend/src/App.tsx`
- `frontend/src/components/InspectionResult.tsx`
- `frontend/src/types.ts`
- `frontend/tsconfig.node.json`
- `frontend/vite.config.ts`
- `ml/MODEL_CARD_TEMPLATE.md`
- `ml/configs/deep_pcb.yaml`
- `reports/validation-summary.json`
- `scripts/download_deeppcb.py`
- `scripts/generate_report_qa_sample.py`
- `scripts/run_phase10_tests.py`
- `scripts/validate_structure.py`
- `scripts/verify_project.py`
- `src/cv/__init__.py`
- `src/cv/alignment.py`
- `src/datasets/__init__.py`
- `src/datasets/converters.py`
- `src/datasets/prepare.py`
- `src/datasets/schema.py`
- `src/datasets/splitting.py`
- `src/inspection/__init__.py`
- `src/inspection/detectors.py`
- `src/inspection/evidence.py`
- `src/inspection/trace_analysis.py`
- `src/ml/__init__.py`
- `src/ml/config.py`
- `src/ml/inference.py`
- `src/ml/metadata.py`
- `src/ml/preflight.py`
- `src/ml/training.py`
- `tests/test_api_phase7.py`
- `tests/test_dataset_converters.py`
- `tests/test_dataset_pipeline.py`
- `tests/test_dataset_schema.py`
- `tests/test_ml_inference.py`
- `tests/test_ml_preflight.py`
- `tests/test_ml_training.py`
- `tests/test_pdf_report.py`
- `tests/test_phase10_contract.py`
- `tests/test_storage.py`
- `tests/test_trace_analysis.py`

Dependency folders, caches, test databases, rendered QA samples and build output are local generated artifacts.
