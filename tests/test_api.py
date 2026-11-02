from io import BytesIO
from pathlib import Path
from unittest.mock import Mock

import numpy as np
import pytest
from fastapi.testclient import TestClient
from PIL import Image

from food11 import serve


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setenv("SKIP_MODEL", "1")
    loader = Mock(side_effect=AssertionError("Unit tests must not load MLflow models"))
    monkeypatch.setattr(serve.mlflow.pyfunc, "load_model", loader)
    with TestClient(serve.app) as client:
        yield client
    loader.assert_not_called()


def image_bytes():
    buffer = BytesIO()
    Image.new("RGB", (128, 128), "white").save(buffer, format="JPEG")
    return buffer.getvalue()


def test_health_and_unavailable(client):
    assert client.get("/health").status_code == 200
    assert (
        client.post(
            "/predict", files={"file": ("image.jpg", image_bytes(), "image/jpeg")}
        ).status_code
        == 503
    )


def assert_prediction(client, monkeypatch, content):
    fake = Mock()
    fake.predict.return_value = np.array([[9.0] + [0.0] * 10])
    monkeypatch.setattr(serve, "model", fake)
    response = client.post(
        "/predict", files={"file": ("bread.jpg", content, "image/jpeg")}
    )
    assert response.status_code == 200
    assert response.json()["category"] == "Bread"
    assert 0 <= response.json()["confidence"] <= 1
    assert fake.predict.call_args.args[0].shape == (1, 3, 224, 224)


def test_predict_generated_image(client, monkeypatch):
    assert_prediction(client, monkeypatch, image_bytes())


def test_predict_food11_fixture(client, monkeypatch):
    fixture = Path(__file__).parent / "fixtures" / "bread.jpg"
    if not fixture.exists():
        pytest.skip("Food-11 data unavailable; real bread fixture still required")
    assert_prediction(client, monkeypatch, fixture.read_bytes())


def test_bad_image(client, monkeypatch):
    monkeypatch.setattr(serve, "model", Mock())
    assert (
        client.post(
            "/predict", files={"file": ("bad.jpg", b"invalid", "image/jpeg")}
        ).status_code
        == 400
    )


def test_normal_startup_loads_champion(monkeypatch):
    monkeypatch.delenv("SKIP_MODEL", raising=False)
    expected = Mock()
    loader = Mock(return_value=expected)
    monkeypatch.setattr(serve.mlflow.pyfunc, "load_model", loader)
    monkeypatch.setattr(serve.mlflow, "set_tracking_uri", Mock())
    monkeypatch.setattr(serve, "model", None)
    serve.load_model()
    loader.assert_called_once_with("models:/food11@champion")
    assert serve.model is expected
