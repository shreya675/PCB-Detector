# Testing

```bash
make check        # ruff + compile check + full pytest suite
pytest -q         # tests only
cd frontend && npm run typecheck && npm run build
docker compose config --quiet
```

API tests skip automatically when FastAPI/SQLAlchemy are not installed; PDF tests need `pymupdf`
(in the `[dev]` extras). The same checks run in GitHub Actions on every push (`.github/workflows/ci.yml`).

Unit tests use synthetic images to exercise geometry and failure handling. Model accuracy is measured
separately on the held-out DeepPCB test split with `python -m src.ml.cli evaluate` and
`scripts/analyze_errors.py`; the results are recorded in `models/model_card.json`.
