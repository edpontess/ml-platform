import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler

from ml_platform.config import TrainingConfig
from ml_platform.features import build_pipeline


def test_pipeline_structure():
    config = TrainingConfig()

    pipeline = build_pipeline(config)

    assert isinstance(
        pipeline.named_steps["scaler"],
        StandardScaler,
    )

    assert isinstance(
        pipeline.named_steps["classifier"],
        LogisticRegression,
    )


def test_model_configuration():
    config = TrainingConfig(
        C=0.5,
        max_iter=500,
        random_state=123,
    )

    pipeline = build_pipeline(config)
    classifier = pipeline.named_steps["classifier"]

    assert classifier.C == 0.5
    assert classifier.max_iter == 500
    assert classifier.random_state == 123


def test_pipeline_training():
    rng = np.random.default_rng(42)

    X = rng.normal(size=(40, 5))
    y = np.array([0, 1] * 20)

    pipeline = build_pipeline(TrainingConfig())
    pipeline.fit(X, y)

    predictions = pipeline.predict(X)

    assert len(predictions) == len(y)
    assert set(predictions).issubset({0, 1})
