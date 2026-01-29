import numpy as np
import pytest
from sklearn.svm import SVC

from msffs.api import msffs_select
from msffs.validation import validate_inputs


def _toy_data():
    X = np.array(
        [
            [0.1, 0.2, 0.3],
            [0.2, 0.1, 0.4],
            [0.15, 0.25, 0.35],
            [0.9, 0.8, 0.7],
            [0.8, 0.9, 0.6],
            [0.85, 0.75, 0.65],
        ]
    )
    y = np.array([0, 0, 0, 1, 1, 1])
    return X, y


def test_validate_inputs_rejects_invalid_k():
    X, _ = _toy_data()
    with pytest.raises(ValueError):
        validate_inputs(X, 0)
    with pytest.raises(ValueError):
        validate_inputs(X, 10)


def test_msffs_select_requires_y():
    X, _ = _toy_data()
    with pytest.raises(ValueError, match="y is required"):
        msffs_select(
            X,
            k=2,
            estimator=SVC(),
            grid_params={"param_grid": {"C": [1.0], "kernel": ["linear"]}, "cv": 2},
        )


def test_msffs_select_requires_estimator_and_grid_params():
    X, y = _toy_data()
    msffs_select(X, k=2, y=y)


def test_msffs_select_rejects_unexpected_kwargs():
    X, y = _toy_data()
    with pytest.raises(TypeError, match="unexpected keyword argument"):
        msffs_select(
            X,
            k=2,
            y=y,
            estimator=SVC(),
            grid_params={"param_grid": {"C": [1.0], "kernel": ["linear"]}, "cv": 2},
            extra_param=1,
        )


def test_msffs_select_rejects_mismatched_y():
    X, y = _toy_data()
    with pytest.raises(ValueError, match="same number of rows"):
        msffs_select(X, k=2, y=y[:-1])
