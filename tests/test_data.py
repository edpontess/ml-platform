import numpy as np
import pytest

from ml_platform.data import load_split, load_train_validation


def test_load_train_data():
    X, y, subjects = load_split("train")

    assert len(X) == len(y) == len(subjects)
    assert X.shape[1] == 561
    assert not X.isna().any().any()
    assert np.isfinite(X.to_numpy()).all()


def test_invalid_split():
    with pytest.raises(ValueError):
        load_split("invalid")


def test_subject_disjoint_split():
    X_train, X_val, y_train, y_val, train_subjects, val_subjects = (
        load_train_validation()
    )

    assert len(X_train) == len(y_train)
    assert len(X_val) == len(y_val)

    assert set(X_train.index).isdisjoint(set(X_val.index))
    assert set(train_subjects).isdisjoint(set(val_subjects))

    _, _, subjects = load_split("train")

    train_subjects = set(subjects.loc[X_train.index])
    val_subjects = set(subjects.loc[X_val.index])

    assert train_subjects.isdisjoint(val_subjects)


def test_reproducible_split():
    split1 = load_train_validation(random_state=42)
    split2 = load_train_validation(random_state=42)

    for data1, data2 in zip(split1, split2):
        assert data1.equals(data2)
