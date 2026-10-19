from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from ml_platform.api import app



@pytest.fixture
def client():
    model = MagicMock()
    model.predict.return_value = [5]

    with patch(
        "ml_platform.api.mlflow.pyfunc.load_model",
        return_value=model,
    ):
        with TestClient(app) as test_client:
            yield test_client, model

    app.state.model = None


def test_health(client):
    test_client, _ = client

    response = test_client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "healthy",
        "model_loaded": True,
    }


def test_predict(client):
    test_client, model = client

    response = test_client.post(
        "/predict",
        json={"features": [0.5] * 561},
    )

    assert response.status_code == 200
    assert response.json() == {
        "prediction": 5,
        "activity": "STANDING",
    }

    model.predict.assert_called_once()


def test_rejects_wrong_feature_count(client):
    test_client, model = client

    response = test_client.post(
        "/predict",
        json={"features": [0.5] * 10},
    )

    assert response.status_code == 422
    model.predict.assert_not_called()


def test_rejects_missing_features(client):
    test_client, model = client

    response = test_client.post("/predict", json={})

    assert response.status_code == 422
    model.predict.assert_not_called()


def test_rejects_invalid_feature_values(client):
    test_client, model = client

    response = test_client.post(
        "/predict",
        json={"features": ["invalid"] * 561},
    )

    assert response.status_code == 422
    model.predict.assert_not_called()


def test_unknown_prediction_class(client):
    test_client, model = client
    model.predict.return_value = [99]

    response = test_client.post(
        "/predict",
        json={"features": [0.5] * 561},
    )

    assert response.status_code == 500
    assert response.json()["detail"] == (
        "Model returned an unknown activity class"
    )


def test_model_unavailable(client):
    test_client, _ = client

    app.state.model = None

    response = test_client.post(
        "/predict",
        json={"features": [0.5] * 561},
    )

    assert response.status_code == 503
    assert response.json()["detail"] == "Model is not available"
