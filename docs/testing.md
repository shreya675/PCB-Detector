# Testing and validation

## Commands

```bash
make test              # full Pytest suite after installing dependencies
make test-phase2       # dataset pipeline
make test-phase3       # YOLO wrappers
make test-phase4       # preprocessing and registration
make test-phase5       # component comparison
make test-phase6       # trace evidence
make test-phase7       # backend; API cases require FastAPI and SQLAlchemy
make test-phase8       # dashboard/API contract
make test-phase9       # PDF reports
make test-phase10      # deployment and taxonomy contracts
make verify            # dependency-aware aggregate verifier
```

`make verify` runs structure, compilation, lint, and the full Pytest suite once.
It saves observed results to `reports/validation-summary.json` and JUnit XML under
`reports/generated`. Install `.[dev]` first. Skips and failures remain separate;
phase-specific legacy runners do not replace the full regression suite.

Frontend verification: `cd frontend && npm ci && npm run build`.
Container configuration: `docker compose config --quiet`; runtime validation
requires a running Docker engine. See `docs/workspace-audit.md` for this audit's
actual results and limits.

Synthetic images validate geometry and failure handling; they do not establish real-world model performance. Accuracy must come from held-out dataset evaluation using the Phase 3 workflow.
