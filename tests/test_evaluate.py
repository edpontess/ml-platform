import numpy as np
import pytest
from sklearn.dummy import DummyClassifier

from ml_platform.evaluate import evaluate_model


def test_evaluate_model():
    X = np.array(
        [
            [0],
            [1],
            [2],
            [3],
            [4],
            [5],
            [6],
            [7],
        ]
    )

    y = np.array([0, 0, 0, 0, 1, 1, 1, 1])

    model = DummyClassifier(strategy="most_frequent")
    model.fit(X, y)

    metrics = evaluate_model(model, X, y)

    expected_metrics = {
        "accuracy",
        "precision_macro",
        "recall_macro",
        "f1_macro",
    }

    assert set(metrics) == expected_metrics

    for value in metrics.values():
        assert isinstance(value, float)
        assert 0.0 <= value <= 1.0


def test_perfect_predictions():
    class PerfectModel:
        def predict(self, X):
            return np.array([0, 1, 0, 1])

    X = np.zeros((4, 2))
    y = np.array([0, 1, 0, 1])

    metrics = evaluate_model(PerfectModel(), X, y)

    assert metrics["accuracy"] == pytest.approx(1.0)
    assert metrics["f1_macro"] == pytest.approx(1.0)
    assert metrics["precision_macro"] == pytest.approx(1.0)
    assert metrics["recall_macro"] == pytest.approx(1.0)
