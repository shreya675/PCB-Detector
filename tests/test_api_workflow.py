"""Exercise persistence and real report generation; only the model is a test double."""
from unittest.mock import patch

import cv2
import numpy as np
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app.api.routes import inspections
from backend.app.db.base import Base
from backend.app.db.session import get_db
from backend.app.main import app
from backend.app.services.contracts import DefectFinding
from backend.app.services.detector import ModelUnavailableError
from backend.app.services.inspection_engine import InspectionEngine
from backend.app.services.storage import InspectionStorage
from tests.test_inspection_engine import FakeDetector


@pytest.fixture
def client(tmp_path, monkeypatch):
    engine = create_engine('sqlite://', connect_args={'check_same_thread': False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    sessions = sessionmaker(engine)

    def database():
        with sessions() as session:
            yield session

    app.dependency_overrides[get_db] = database
    monkeypatch.setattr(inspections, 'storage', InspectionStorage(tmp_path))
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.pop(get_db, None)
    engine.dispose()


def upload(width=120, height=100):
    ok, encoded = cv2.imencode('.png', np.full((height, width, 3), 120, np.uint8))
    assert ok
    return {'test_image': ('board.png', encoded.tobytes(), 'image/png')}


@pytest.mark.parametrize('findings, expected', [
    ((), 'PASS'),
    ((DefectFinding('spur', (10, 10, 25, 25), .8, 'test'),), 'PASS WITH WARNING'),
    ((DefectFinding('short_circuit', (10, 10, 25, 25), .9, 'test'),
      DefectFinding('spur', (30, 30, 40, 40), .7, 'test')), 'FAIL'),
])
def test_complete_inspection_workflow(client, monkeypatch, findings, expected):
    detector = FakeDetector(findings)
    monkeypatch.setattr(inspections, 'detector', detector)
    monkeypatch.setattr(inspections, 'inspection_engine', InspectionEngine(detector, inspections.policy))
    response = client.post('/api/inspect', files=upload())
    assert response.status_code == 201, response.text
    record = response.json()
    assert record['status'] == expected
    assert record['created_at'].endswith(('Z', '+00:00'))
    assert len(record['defects']) == len(findings)
    identifier = record['id']
    assert client.get(f'/api/inspections/{identifier}').json()['id'] == identifier
    history = client.get('/api/inspections?limit=1').json()
    assert history['total'] == 1
    assert len(history['items']) == 1
    assert client.get(f'/api/inspections/{identifier}/image/annotated').status_code == 200
    report = client.get(f'/api/inspections/{identifier}/report')
    assert report.headers['content-type'] == 'application/pdf'
    assert report.content.startswith(b'%PDF')


def test_missing_model_returns_503_without_saving_pass(client):
    with patch.object(inspections.inspection_engine, 'inspect', side_effect=ModelUnavailableError('Missing weights')):
        assert client.post('/api/inspect', files=upload()).status_code == 503
    assert client.get('/api/inspections').json()['total'] == 0


def test_tiny_image_returns_validation_error(client):
    assert client.post('/api/inspect', files=upload(1, 1)).status_code == 422
