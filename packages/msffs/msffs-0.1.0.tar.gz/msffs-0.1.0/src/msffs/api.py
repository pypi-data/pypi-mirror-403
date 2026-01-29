from collections.abc import Mapping
from typing import Any, TypedDict

import numpy as np
from numpy.typing import ArrayLike
from sklearn.base import BaseEstimator
from sklearn.linear_model import LogisticRegression

from ._msffs_impl import msffs_run
from .validation import validate_inputs


class MSFFSResult(TypedDict, total=False):
    selected_indices: np.ndarray
    selected_X: np.ndarray
    best_scores: np.ndarray
    winner_list: list[list[int]]
    best_params_list: list[Any]


def _default_estimator() -> BaseEstimator:
    # Keep defaults lightweight and deterministic for common classification tasks.
    return LogisticRegression(max_iter=1000, random_state=0)


def _default_grid_params() -> Mapping[str, Any]:
    return {
        "param_grid": {"C": [0.1, 1.0, 10.0]},
        "cv": 3,
    }


def _coerce_target(y: ArrayLike) -> np.ndarray:
    y_arr = np.asarray(y)
    if y_arr.ndim == 2 and y_arr.shape[1] == 1:
        y_arr = y_arr[:, 0]
    if y_arr.ndim != 1:
        raise ValueError("y must be a 1D array-like (or shape (n_samples, 1)).")
    return y_arr


def msffs_select(
    X: ArrayLike,
    k: int,
    y: ArrayLike | None = None,
    estimator: BaseEstimator | None = None,
    grid_params: Mapping[str, Any] | None = None,
) -> MSFFSResult:
    """Run mSFFS feature selection and return selection details.

    Parameters
    ----------
    X : array-like of shape (n_samples, n_features)
        Input feature matrix.
    k : int
        Number of features to select.
    y : array-like of shape (n_samples,), required
        Target labels.
    estimator : sklearn estimator, optional
        Base estimator to tune with GridSearchCV. Defaults to LogisticRegression.
    grid_params : mapping, optional
        Either a param grid dict or a config dict containing "param_grid" and
        optional GridSearchCV settings (cv, scoring, n_jobs, refit). Defaults
        to a small grid suitable for quick usage.

    Returns
    -------
    MSFFSResult
        Dictionary containing selected indices and search diagnostics.
    """
    if y is None:
        raise ValueError("y is required for mSFFS")

    if estimator is None:
        estimator = _default_estimator()
    if grid_params is None:
        grid_params = _default_grid_params()

    if isinstance(grid_params, Mapping) and "param_grid" in grid_params:
        param_grid = grid_params["param_grid"]
    else:
        param_grid = grid_params
    if param_grid is None or (hasattr(param_grid, "__len__") and len(param_grid) == 0):
        raise ValueError("grid_params must include a non-empty param grid.")

    X, k = validate_inputs(X, k)
    y_arr = _coerce_target(y)
    if y_arr.shape[0] != X.shape[0]:
        raise ValueError("y must have the same number of rows as X.")

    selected = msffs_run(
        X=np.asarray(X),
        y=y_arr,
        max_f=k,
        estimator=estimator,
        grid_params=grid_params,
    )

    selected_indices: list[int] = []
    if 0 <= k < len(selected["winner_list"]):
        selected_indices = selected["winner_list"][k]

    result: MSFFSResult = {
        "selected_indices": np.asarray(selected_indices, dtype=int),
        "best_scores": selected["best_scores"],
        "winner_list": selected["winner_list"],
        "best_params_list": selected["best_params_list"],
    }

    if len(selected_indices) > 0:
        result["selected_X"] = np.asarray(X)[:, selected_indices]

    return result
