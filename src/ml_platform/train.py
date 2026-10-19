import json
from dataclasses import asdict
from pathlib import Path

import mlflow
import mlflow.sklearn

from ml_platform.config import TrainingConfig
from ml_platform.data import load_train_validation
from ml_platform.evaluate import evaluate_model
from ml_platform.features import build_pipeline


def main():
    config = TrainingConfig(C=10.0)

    mlflow.set_tracking_uri("http://127.0.0.1:5001")
    mlflow.set_experiment("human-activity-recognition")

    with mlflow.start_run(run_name="logistic-regression-baseline"):
        mlflow.log_params(asdict(config))
        mlflow.set_tag("model_type", "logistic_regression")
        mlflow.set_tag("dataset", "UCI_HAR")

        print("Loading dataset...")

        X_train, X_val, y_train, y_val, train_subjects, val_subjects = (
            load_train_validation(
                test_size=config.validation_size,
                random_state=config.random_state,
            )
        )

        print("Training model...")

        model = build_pipeline(config)
        model.fit(X_train, y_train)

        print("Evaluating model...")

        metrics = evaluate_model(model, X_val, y_val)

        mlflow.log_metrics(metrics)
        mlflow.log_param("train_samples", len(X_train))
        mlflow.log_param("validation_samples", len(X_val))
        mlflow.log_param("train_subjects", len(train_subjects))
        mlflow.log_param("validation_subjects", len(val_subjects))

        print("Logging model to MLflow...")

        mlflow.sklearn.log_model(
            sk_model=model,
            name="model",
            input_example=X_train.head(3),
        )

        Path("reports").mkdir(exist_ok=True)

        metrics_path = Path("reports/validation_metrics.json")
        metrics_path.write_text(json.dumps(metrics, indent=2))

        mlflow.log_artifact(str(metrics_path))

        for name, value in metrics.items():
            print(f"{name}: {value:.4f}")

        print(f"MLflow run ID: {mlflow.active_run().info.run_id}")


if __name__ == "__main__":
    main()
