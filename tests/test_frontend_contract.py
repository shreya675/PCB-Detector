import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class FrontendContractTests(unittest.TestCase):
    def test_required_dashboard_views_exist(self):
        app = (ROOT / "frontend/src/App.tsx").read_text()
        for label in ("Inspection overview", "New inspection", "Inspection history", "Defect analytics", "Model performance"):
            self.assertIn(label, app)

    def test_upload_contract_matches_backend(self):
        api = (ROOT / "frontend/src/lib/api.ts").read_text()
        self.assertIn('body.append("test_image", test)', api)
        self.assertIn('body.append("reference_image", reference)', api)
        self.assertIn('request<Inspection>("/api/inspect"', api)

    def test_no_placeholder_metrics(self):
        panel = (ROOT / "frontend/src/components/ModelPanel.tsx").read_text()
        self.assertIn("No evaluated project model available", panel)
        self.assertIn('request<ModelInfo>("/api/model")', (ROOT / "frontend/src/lib/api.ts").read_text())
        for source in (panel, (ROOT / "frontend/src/App.tsx").read_text()):
            self.assertNotIn("98.6%", source)
            self.assertNotIn("99.9%", source)

    def test_responsive_and_accessibility_rules_exist(self):
        css = (ROOT / "frontend/src/styles.css").read_text()
        self.assertIn("@media(max-width:760px)", css)
        self.assertIn("prefers-reduced-motion", css)
        self.assertIn("overflow-x:auto", css)
        self.assertIn("min-height:44px", css)

    def test_backend_exposes_safe_artifact_route(self):
        route = (ROOT / "backend/app/api/routes/inspections.py").read_text()
        self.assertIn('/inspections/{inspection_id}/image/{kind}', route)
        self.assertIn('kind not in {"test", "reference", "annotated"}', route)
