"""Run with the Phase 7 API dependencies installed."""
import importlib.util
import os
import tempfile
import unittest
from pathlib import Path

HAS_API_DEPS = all(importlib.util.find_spec(name) for name in ("fastapi", "sqlalchemy", "pydantic_settings"))
_TEMP_ROOT = Path(tempfile.mkdtemp(prefix="pcb-aoi-api-tests-"))
os.environ["DATABASE_URL"] = f"sqlite:///{_TEMP_ROOT / 'test.db'}"
os.environ["STORAGE_ROOT"] = str(_TEMP_ROOT / "reports")


@unittest.skipUnless(HAS_API_DEPS, "FastAPI/SQLAlchemy dependencies are not installed in this sandbox")
class ApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from fastapi.testclient import TestClient

        from backend.app.db.base import Base
        from backend.app.db.session import engine
        from backend.app.main import app
        Base.metadata.create_all(bind=engine)
        cls.client = TestClient(app)

    def test_health_endpoint(self):
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["database"], "ok")

    def test_history_is_paginated(self):
        response = self.client.get("/api/inspections?limit=10&offset=0")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["items"], [])

    def test_unknown_inspection_is_404(self):
        response = self.client.get("/api/inspections/00000000-0000-0000-0000-000000000000")
        self.assertEqual(response.status_code, 404)

    def test_invalid_upload_is_422(self):
        response = self.client.post("/api/inspect", files={"test_image": ("bad.png", b"corrupt", "image/png")})
        self.assertEqual(response.status_code, 422)
