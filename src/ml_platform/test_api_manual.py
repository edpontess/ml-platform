import httpx

from ml_platform.data import load_split


def main():
    X_test, y_test, _ = load_split("test")

    sample = X_test.iloc[0].tolist()
    actual = int(y_test.iloc[0])

    response = httpx.post(
        "http://127.0.0.1:8000/predict",
        json={"features": sample},
        timeout=30.0,
    )

    response.raise_for_status()

    print("Actual class:", actual)
    print("API response:", response.json())


if __name__ == "__main__":
    main()