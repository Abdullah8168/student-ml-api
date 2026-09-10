import pytest
from fastapi.testclient import TestClient

from app import APP_VERSION, MODEL_VERSION, app

client = TestClient(app)


def test_health_returns_status_and_version():
    response = client.get("/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["application"] == "student-ml-api"
    assert data["application_version"] == APP_VERSION


def test_health_reports_model_version():
    data = client.get("/health").json()

    assert data["model_version"] == MODEL_VERSION == "model-1"
    assert set(data) == {"status", "application", "application_version", "model_version"}


def test_health_version_matches_version_file():
    with open("VERSION", encoding="utf-8") as f:
        assert client.get("/health").json()["application_version"] == f.read().strip()


@pytest.mark.parametrize(
    "value, expected",
    [(10, 20), (0, 0), (-3, -6), (2.5, 5.0)],
)
def test_predict_success(value, expected):
    response = client.post("/predict", json={"value": value})

    assert response.status_code == 200
    assert response.json() == {"input": value, "prediction": expected}


def test_predict_missing_input_is_rejected():
    response = client.post("/predict", json={})

    assert response.status_code == 422
    assert response.json()["detail"][0]["loc"] == ["body", "value"]


@pytest.mark.parametrize("bad_value", ["abc", "10", None, True, [1, 2]])
def test_predict_invalid_input_is_rejected(bad_value):
    response = client.post("/predict", json={"value": bad_value})

    assert response.status_code == 422


def test_predict_requires_json_body():
    response = client.post("/predict")

    assert response.status_code == 422
