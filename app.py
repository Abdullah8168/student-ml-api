"""student-ml-api: a minimal ML inference service."""

from pathlib import Path
from typing import Union

from fastapi import FastAPI
from pydantic import BaseModel, StrictFloat, StrictInt

APP_NAME = "student-ml-api"
# Versioned independently of the application: the same app release could serve a retrained model.
MODEL_VERSION = "model-1"
VERSION_FILE = Path(__file__).resolve().parent / "VERSION"


def read_version() -> str:
    """Single source of truth for the application version is the VERSION file."""
    return VERSION_FILE.read_text(encoding="utf-8").strip()


APP_VERSION = read_version()

app = FastAPI(title=APP_NAME, version=APP_VERSION)


class PredictionRequest(BaseModel):
    # Strict types: reject strings like "10" and booleans instead of silently coercing them.
    value: Union[StrictInt, StrictFloat]


class PredictionResponse(BaseModel):
    input: Union[int, float]
    prediction: Union[int, float]


def predict(value: Union[int, float]) -> Union[int, float]:
    """Placeholder model: a linear function y = 2x."""
    return value * 2


@app.get("/health")
def health() -> dict:
    return {
        "status": "healthy",
        "application": APP_NAME,
        "application_version": APP_VERSION,
        "model_version": MODEL_VERSION,
    }


@app.post("/predict", response_model=PredictionResponse)
def predict_endpoint(request: PredictionRequest) -> PredictionResponse:
    return PredictionResponse(input=request.value, prediction=predict(request.value))
