import json

from fastapi.testclient import TestClient

from backend.app.api.routes import model as model_route
from backend.app.main import app


def test_model_endpoint_shape() -> None:
    payload = TestClient(app).get("/api/model").json()
    assert payload["model_status"] in {"available", "missing"}
    assert set(payload["postprocess"]) == {"enabled", "nms_iou", "box_scale"}
    assert "evaluation" in payload and "evaluation_mismatch" in payload


def test_model_card_hidden_when_weights_differ(tmp_path, monkeypatch) -> None:
    card = tmp_path / "card.json"
    card.write_text(json.dumps({"name": "x", "weights": {"sha256": "deadbeef"}}))
    weights = tmp_path / "w.pt"
    weights.write_bytes(b"not-a-real-checkpoint")
    monkeypatch.setattr(model_route.settings, "model_path", str(weights))
    monkeypatch.setattr(model_route.settings, "model_card_path", str(card))
    payload = TestClient(app).get("/api/model").json()
    assert payload["model_status"] == "available"
    assert payload["evaluation"] is None
    assert payload["evaluation_mismatch"] is True


def test_model_card_shown_when_checksum_matches(tmp_path, monkeypatch) -> None:
    from src.ml.metadata import sha256_file

    weights = tmp_path / "w.pt"
    weights.write_bytes(b"not-a-real-checkpoint")
    card = tmp_path / "card.json"
    card.write_text(json.dumps({"name": "x", "weights": {"sha256": sha256_file(weights)}}))
    monkeypatch.setattr(model_route.settings, "model_path", str(weights))
    monkeypatch.setattr(model_route.settings, "model_card_path", str(card))
    payload = TestClient(app).get("/api/model").json()
    assert payload["evaluation"]["name"] == "x"
    assert payload["evaluation_mismatch"] is False
