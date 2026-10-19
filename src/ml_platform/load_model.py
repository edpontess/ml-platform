import mlflow
import mlflow.pyfunc

from ml_platform.data import load_split


def main():
    mlflow.set_tracking_uri("http://127.0.0.1:5001")

    model = mlflow.pyfunc.load_model("models:/human-activity-classifier@champion")

    X_test, _, _ = load_split("test")

    predictions = model.predict(X_test.head(5))

    print("Predictions:", predictions)


if __name__ == "__main__":
    main()
