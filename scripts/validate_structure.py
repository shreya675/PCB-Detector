import sys
from pathlib import Path

root = Path(__file__).resolve().parents[1]
required = [
    "backend/app/main.py", "frontend/src/main.tsx", "ml/configs/deep_pcb.yaml",
    "src/cv/__init__.py", "src/inspection/__init__.py", "data/raw/.gitkeep",
    "data/interim/.gitkeep", "data/processed/.gitkeep", "models/weights/.gitkeep",
    "reports/generated/.gitkeep", "tests/test_project_structure.py", "docs/architecture.md",
    "src/datasets/cli.py", "src/datasets/prepare.py", "docs/datasets.md",
    "src/ml/cli.py", "src/ml/training.py", "src/ml/inference.py",
    "ml/configs/yolo_baseline.yaml", "docs/model-training.md",
    "src/cv/alignment.py", "src/cv/difference.py", "src/cv/cli.py",
    "docs/image-registration.md",
    "src/inspection/comparison.py", "src/inspection/detectors.py",
    "src/inspection/cli.py", "docs/component-comparison.md",
    "src/inspection/trace_analysis.py", "src/inspection/evidence.py",
    "src/inspection/trace_cli.py", "docs/advanced-trace-analysis.md",
    "backend/app/api/routes/inspections.py", "backend/app/db/models.py",
    "backend/app/services/inspection_engine.py", "backend/app/services/severity.py",
    "backend/app/core/severity.yaml", "docs/backend-api.md",
    "frontend/src/App.tsx", "frontend/src/lib/api.ts",
    "frontend/src/components/InspectionResult.tsx", "docs/frontend-dashboard.md",
    "backend/app/services/pdf_report.py", "docs/pdf-reports.md",
    "Dockerfile", "docker-compose.yml", "frontend/Dockerfile", "frontend/nginx.conf",
    ".github/workflows/ci.yml", "alembic.ini", "migrations/env.py",
    "migrations/versions/0001_initial_schema.py", "docs/testing.md",
    "docs/deployment.md", "docs/model-classes.md", "SECURITY.md", "LICENSE",
]
missing = [item for item in required if not (root / item).exists()]
if missing:
    print("Missing required paths:")
    print("\n".join(f"- {item}" for item in missing))
    sys.exit(1)
print(f"Phase 1 structure valid ({len(required)} required paths checked).")
