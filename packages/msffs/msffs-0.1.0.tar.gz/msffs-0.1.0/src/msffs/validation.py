import numpy as np


def validate_inputs(X, k) -> tuple[np.ndarray, int]:
    X = np.asarray(X)
    if X.ndim != 2:
        raise ValueError("X must be a 2D array")

    if not isinstance(k, (int, np.integer)):
        raise ValueError("k must be an integer")

    if k <= 0:
        raise ValueError("k must be positive")
    if k > X.shape[1]:
        raise ValueError("k cannot exceed number of features in X")

    return X, k
