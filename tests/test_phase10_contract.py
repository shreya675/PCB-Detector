import json
import unittest
from pathlib import Path

import yaml

from src.datasets.schema import CLASS_NAMES

ROOT = Path(__file__).resolve().parents[1]


class Phase10ContractTests(unittest.TestCase):
    def test_taxonomy_preserves_distinct_hole_defects(self):
        self.assertEqual(len(CLASS_NAMES), 7)
        self.assertEqual(
            CLASS_NAMES,
            ("open_circuit", "short_circuit", "spur", "spurious_copper", "mouse_bite", "missing_hole", "pin_hole"),
        )

    def test_yolo_config_uses_canonical_order(self):
        config = yaml.safe_load((ROOT / "ml/configs/deep_pcb.yaml").read_text())
        self.assertEqual(tuple(config["names"].values()), CLASS_NAMES)

    def test_trained_weights_are_not_committed(self):
        # Weights live on disk locally but must stay out of git; the model card documents them instead.
        gitignore = (ROOT / ".gitignore").read_text()
        self.assertIn("models/weights/*", gitignore)
        self.assertIn("!models/weights/.gitkeep", gitignore)
        card = json.loads((ROOT / "models/model_card.json").read_text())
        self.assertEqual(len(card["weights"]["sha256"]), 64)

    def test_docker_runs_as_non_root_with_healthcheck(self):
        dockerfile = (ROOT / "Dockerfile").read_text()
        self.assertIn("USER aoi", dockerfile)
        self.assertIn("HEALTHCHECK", dockerfile)
        self.assertIn("alembic upgrade head", dockerfile)
        self.assertIn('pip install -e ".[postgres]"', dockerfile)

    def test_frontend_container_is_unprivileged(self):
        dockerfile = (ROOT / "frontend/Dockerfile").read_text()
        self.assertIn("nginxinc/nginx-unprivileged", dockerfile)
        self.assertIn("npm run build", dockerfile)

    def test_compose_has_three_services_and_health_dependencies(self):
        compose = yaml.safe_load((ROOT / "docker-compose.yml").read_text())
        self.assertEqual(set(compose["services"]), {"api", "db", "frontend"})
        self.assertEqual(
            compose["services"]["api"]["depends_on"]["db"]["condition"],
            "service_healthy",
        )

    def test_ci_covers_backend_frontend_and_containers(self):
        workflow = yaml.safe_load((ROOT / ".github/workflows/ci.yml").read_text())
        self.assertEqual(set(workflow["jobs"]), {"backend", "frontend", "containers"})

    def test_frontend_defaults_to_same_origin(self):
        api = (ROOT / "frontend/src/lib/api.ts").read_text()
        self.assertIn('VITE_API_BASE_URL || ""', api)

    def test_initial_migration_has_both_tables(self):
        migration = (ROOT / "migrations/versions/0001_initial_schema.py").read_text()
        self.assertIn('"inspections"', migration)
        self.assertIn('"defects"', migration)
        self.assertIn("ondelete=\"CASCADE\"", migration)

    def test_versions_are_consistent(self):
        package = json.loads((ROOT / "frontend/package.json").read_text())
        self.assertEqual(package["version"], "1.0.0")
        self.assertIn('version="1.0.0"', (ROOT / "backend/app/main.py").read_text())
        self.assertIn('"version": "1.0.0"', (ROOT / "backend/app/api/routes/health.py").read_text())

    def test_safety_documentation_is_explicit(self):
        text = "\n".join(
            (ROOT / name).read_text()
            for name in ["README.md", "SECURITY.md", "docs/model-classes.md"]
        ).lower()
        for phrase in ["no trained", "not an industrial", "authentication", "output taxonomy"]:
            self.assertIn(phrase, text)


if __name__ == "__main__":
    unittest.main()
