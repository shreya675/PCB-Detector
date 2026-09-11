.PHONY: install install-ml api frontend test test-phase2 test-phase3 test-phase4 test-phase5 test-phase6 test-phase7 test-phase8 test-phase9 test-phase10 verify migrate docker-up docker-down cv-align trace-analyze component-compare ml-preflight ml-train lint validate

install:
	python -m pip install -e ".[dev]"
	cd frontend && npm install

install-ml:
	python -m pip install -e ".[ml]"

api:
	uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000

frontend:
	cd frontend && npm run dev

test:
	pytest

test-phase2:
	python scripts/run_phase2_tests.py

test-phase3:
	python scripts/run_phase3_tests.py

test-phase4:
	python scripts/run_phase4_tests.py

test-phase5:
	python scripts/run_phase5_tests.py

test-phase6:
	python scripts/run_phase6_tests.py

test-phase7:
	python scripts/run_phase7_tests.py

test-phase8:
	python scripts/run_phase8_tests.py

test-phase9:
	python scripts/run_phase9_tests.py

test-phase10:
	python scripts/run_phase10_tests.py

verify:
	python scripts/verify_project.py

migrate:
	alembic upgrade head

docker-up:
	docker compose up --build

docker-down:
	docker compose down

cv-align:
	python -m src.cv.cli --reference samples/reference.png --test samples/test.png

component-compare:
	python -m src.inspection.cli --reference samples/reference.png --test samples/test.png

trace-analyze:
	python -m src.inspection.trace_cli --reference samples/reference.png --test samples/test.png

ml-preflight:
	python -m src.ml.cli preflight --config ml/configs/yolo_baseline.yaml

ml-train:
	python -m src.ml.cli train --config ml/configs/yolo_baseline.yaml

lint:
	ruff check .

validate:
	python scripts/validate_structure.py
	python -m compileall -q backend src tests scripts migrations
