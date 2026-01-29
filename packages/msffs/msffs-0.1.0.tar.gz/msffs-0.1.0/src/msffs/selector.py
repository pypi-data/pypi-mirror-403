from collections.abc import Mapping
from typing import Any

import numpy as np
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.feature_selection import SelectorMixin
from sklearn.utils.validation import check_is_fitted

from .api import msffs_select


class MSFFSSelector(BaseEstimator, SelectorMixin, TransformerMixin):
    """Scikit-learn compatible transformer that selects k features via mSFFS."""

    def __init__(
        self,
        k: int,
        estimator: BaseEstimator | None = None,
        grid_params: Mapping[str, Any] | None = None,
    ) -> None:
        self.k = k
        self.estimator = estimator
        self.grid_params = grid_params

    def fit(self, X, y: np.ndarray | None = None):
        """Fit the selector and compute the feature mask."""
        if y is None:
            raise ValueError("y is required for mSFFS")

        X_arr = np.asarray(X)
        result = msffs_select(
            X_arr,
            k=self.k,
            y=y,
            estimator=self.estimator,
            grid_params=self.grid_params,
        )

        self.n_features_in_ = X_arr.shape[1]
        self.selected_idx_ = np.asarray(result["selected_indices"], dtype=int)
        support = np.zeros(self.n_features_in_, dtype=bool)
        support[self.selected_idx_] = True
        self.support_ = support
        self.best_scores_ = result["best_scores"]
        self.winner_list_ = result["winner_list"]
        self.best_params_list_ = result["best_params_list"]
        return self

    def _get_support_mask(self):
        check_is_fitted(self, "support_")
        return self.support_

    def transform(self, X):
        check_is_fitted(self, "selected_idx_")
        X_arr = np.asarray(X)
        return X_arr[:, self.selected_idx_]
