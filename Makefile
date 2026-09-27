.PHONY: install install-ml api frontend test migrate docker-up docker-down cv-align trace-analyze component-compare ml-preflight ml-train lint check

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

check:
	ruff check backend src tests scripts
	python -m compileall -q backend src tests scripts migrations
	pytest
