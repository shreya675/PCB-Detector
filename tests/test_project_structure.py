from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_required_phase_one_paths_exist() -> None:
    required = [
        "backend/app/main.py", "frontend/package.json", "ml/configs/deep_pcb.yaml",
        "src/cv", "src/inspection", "data/raw", "models/weights", "reports/generated",
        "docs/architecture.md", ".env.example", "Dockerfile", "docker-compose.yml",
    ]
    missing = [path for path in required if not (ROOT / path).exists()]
    assert not missing, f"Missing scaffold paths: {missing}"
