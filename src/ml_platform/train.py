import json
from pathlib import Path

import joblib

from ml_platform.data import load_split, load_train_validation
from ml_platform.evaluate import evaluate_model
from ml_platform.features import build_pipeline
from ml_platform.config import TrainingConfig


def main():
    print("Loading dataset...")

    X_train, X_val, y_train, y_val, train_subjects, val_subjects = (
        load_train_validation(
            test_size=TrainingConfig().validation_size,
            random_state=TrainingConfig().random_state,
        )
    )

    print(f"Training samples: {len(X_train)}")
    print(f"Validation samples: {len(X_val)}")
    print(f"Training subjects: {len(train_subjects)}")
    print(f"Validation subjects: {len(val_subjects)}")

    print("Training model...")

    config = TrainingConfig()

    model = build_pipeline(config)
    model.fit(X_train, y_train)

    print("Evaluating on validation set...")

    metrics = evaluate_model(model, X_val, y_val)

    for name, value in metrics.items():
        print(f"{name}: {value:.4f}")

    Path("models").mkdir(exist_ok=True)
    Path("reports").mkdir(exist_ok=True)

    joblib.dump(model, "models/model.joblib")

    with open("reports/validation_metrics.json", "w") as f:
        json.dump(metrics, f, indent=2)

    print("Model and validation metrics saved.")
    print("Original test set has not been used.")


if __name__ == "__main__":
    main()
