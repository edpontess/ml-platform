import json
from pathlib import Path

import joblib

from ml_platform.data import load_split
from ml_platform.features import build_pipeline
from ml_platform.evaluate import evaluate_model


def main():
    print("Loading dataset...")

    X_train, y_train, train_subjects = load_split("train")
    X_test, y_test, test_subjects = load_split("test")

    if set(train_subjects) & set(test_subjects):
        raise ValueError("Subject leakage detected")

    print(f"Training samples: {len(X_train)}")
    print(f"Test samples: {len(X_test)}")

    print("Training model...")

    model = build_pipeline()
    model.fit(X_train, y_train)

    print("Evaluating model...")

    metrics = evaluate_model(model, X_test, y_test)

    for name, value in metrics.items():
        print(f"{name}: {value:.4f}")

    Path("models").mkdir(exist_ok=True)
    Path("reports").mkdir(exist_ok=True)

    joblib.dump(model, "models/model.joblib")

    with open("reports/metrics.json", "w") as f:
        json.dump(metrics, f, indent=2)

    print("Model and metrics saved.")


if __name__ == "__main__":
    main()