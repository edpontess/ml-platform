from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.model_selection import GroupShuffleSplit

DATA_DIR = Path("data/human+activity+recognition+using+smartphones/UCI HAR Dataset")


def load_split(split: str):
    if split not in {"train", "test"}:
        raise ValueError("split must be 'train' or 'test'")

    folder = DATA_DIR / split

    X = pd.read_csv(
        folder / f"X_{split}.txt",
        sep=r"\s+",
        header=None,
    )

    y = pd.read_csv(
        folder / f"y_{split}.txt",
        sep=r"\s+",
        header=None,
    ).iloc[:, 0]

    subjects = pd.read_csv(
        folder / f"subject_{split}.txt",
        sep=r"\s+",
        header=None,
    ).iloc[:, 0]

    if len(X) != len(y) or len(X) != len(subjects):
        raise ValueError("Feature, label and subject counts differ")

    if X.isna().any().any() or y.isna().any():
        raise ValueError("Dataset contains missing values")

    if not np.isfinite(X.to_numpy()).all():
        raise ValueError("Dataset contains non-finite features")

    return X, y, subjects


def load_train_validation(test_size=0.2, random_state=42):
    X, y, subjects = load_split("train")

    splitter = GroupShuffleSplit(
        n_splits=1,
        test_size=test_size,
        random_state=random_state,
    )

    train_idx, val_idx = next(
        splitter.split(X, y, groups=subjects)
    )

    X_train = X.iloc[train_idx]
    X_val = X.iloc[val_idx]

    y_train = y.iloc[train_idx]
    y_val = y.iloc[val_idx]

    train_subjects = subjects.iloc[train_idx]
    val_subjects = subjects.iloc[val_idx]

    assert set(train_subjects).isdisjoint(set(val_subjects))

    return X_train, X_val, y_train, y_val, train_subjects, val_subjects