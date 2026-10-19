from contextlib import asynccontextmanager

import mlflow
import mlflow.pyfunc
import numpy as np
import pandas as pd
import os
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel, Field, field_validator

TRACKING_URI = os.getenv(
    "MLFLOW_TRACKING_URI",
    "http://127.0.0.1:5000",
)
MODEL_URI = "models:/human-activity-classifier@champion"

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


@asynccontextmanager
async def lifespan(app: FastAPI):
    mlflow.set_tracking_uri(TRACKING_URI)

    # Load the champion once, when the application starts.
    app.state.model = mlflow.pyfunc.load_model(MODEL_URI)

    yield

    # Release the reference when the application stops.
    app.state.model = None


app = FastAPI(
    title="Human Activity Recognition API",
    description="ML model serving using FastAPI and MLflow",
    version="0.1.0",
    lifespan=lifespan,
)


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

    prediction = int(model.predict(X)[0])

    if prediction not in ACTIVITY_LABELS:
        raise HTTPException(
            status_code=500,
            detail="Model returned an unknown activity class",
        )

    return PredictionResponse(
        prediction=prediction,
        activity=ACTIVITY_LABELS[prediction],
    )