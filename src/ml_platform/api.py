import logging
import os
import time
from contextlib import asynccontextmanager

import mlflow
import mlflow.pyfunc
import numpy as np
import pandas as pd
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel, Field, field_validator

from ml_platform.logging_config import configure_logging

TRACKING_URI = os.getenv(
    "MLFLOW_TRACKING_URI",
    "http://127.0.0.1:5000",
)
MODEL_URI = os.getenv(
    "MODEL_URI",
    "models:/human-activity-classifier@champion",
)

N_FEATURES = 561

ACTIVITY_LABELS = {
    1: "WALKING",
    2: "WALKING_UPSTAIRS",
    3: "WALKING_DOWNSTAIRS",
    4: "SITTING",
    5: "STANDING",
    6: "LAYING",
}


class PredictionRequest(BaseModel):
    features: list[float] = Field(min_length=N_FEATURES, max_length=N_FEATURES)

    @field_validator("features")
    @classmethod
    def validate_features(cls, features):
        if not np.isfinite(features).all():
            raise ValueError("Features must contain only finite values")
        return features


class PredictionResponse(BaseModel):
    prediction: int
    activity: str


configure_logging()
logger = logging.getLogger("ml_platform.api")


@asynccontextmanager
async def lifespan(app: FastAPI):
    mlflow.set_tracking_uri(TRACKING_URI)

    logger.info(
        "Loading model",
        extra={"event": "model_loading"},
    )

    try:
        # Load the champion once, when the application starts.
        app.state.model = mlflow.pyfunc.load_model(MODEL_URI)
    except Exception:
        logger.exception(
            "Failed to load model",
            extra={"event": "model_loading_failed"},
        )
        raise

    logger.info(
        "Model loaded successfully",
        extra={"event": "model_loaded"},
    )

    yield

    # Release the reference when the application stops.
    app.state.model = None

    logger.info(
        "Application shutting down",
        extra={"event": "application_shutdown"},
    )


app = FastAPI(
    title="Human Activity Recognition API",
    description="ML model serving using FastAPI and MLflow",
    version="0.1.0",
    lifespan=lifespan,
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.perf_counter()

    try:
        response = await call_next(request)
    except Exception:
        duration_ms = round(
            (time.perf_counter() - start_time) * 1000,
            2,
        )

        logger.exception(
            "Unhandled HTTP request error",
            extra={
                "event": "http_request",
                "method": request.method,
                "path": request.url.path,
                "status_code": 500,
                "duration_ms": duration_ms,
            },
        )
        raise

    duration_ms = round(
        (time.perf_counter() - start_time) * 1000,
        2,
    )

    logger.info(
        "HTTP request completed",
        extra={
            "event": "http_request",
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "duration_ms": duration_ms,
        },
    )

    return response


@app.get("/health")
def health(request: Request):
    return {
        "status": "healthy",
        "model_loaded": request.app.state.model is not None,
    }


@app.post("/predict", response_model=PredictionResponse)
def predict(payload: PredictionRequest, request: Request):
    model = request.app.state.model

    if model is None:
        raise HTTPException(
            status_code=503,
            detail="Model is not available",
        )

    # One row, 561 features.
    X = pd.DataFrame([payload.features], columns=range(N_FEATURES))

    start_time = time.perf_counter()

    prediction = int(model.predict(X)[0])

    inference_duration_ms = round(
        (time.perf_counter() - start_time) * 1000,
        2,
    )

    logger.info(
        "Model inference completed",
        extra={
            "event": "model_inference",
            "duration_ms": inference_duration_ms,
        },
    )

    if prediction not in ACTIVITY_LABELS:
        raise HTTPException(
            status_code=500,
            detail="Model returned an unknown activity class",
        )

    return PredictionResponse(
        prediction=prediction,
        activity=ACTIVITY_LABELS[prediction],
    )
