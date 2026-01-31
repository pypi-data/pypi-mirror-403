"""
Model-based feature selection.
"""

from __future__ import annotations

from typing import Optional, Union, Literal

import numpy as np

from nalyst.core.foundation import BaseLearner, TransformerMixin
from nalyst.core.validation import check_array, check_is_trained, duplicate


class SelectFromModel(TransformerMixin, BaseLearner):
    """
    Feature selection based on model importance.

    Parameters
    ----------
    estimator : object
        The base estimator to compute feature importances.
    threshold : str or float, optional
        Threshold for selecting features. "mean", "median", or a float.
    prefit : bool, default=False
        Whether estimator is already fitted.
    norm_order : int, default=1
        Order of norm used to aggregate multi-output coef_.
    max_features : int, optional
        Maximum number of features to select.
    importance_getter : str or callable, default="auto"
        How to get feature importances.

    Attributes
    ----------
    estimator_ : object
        Fitted estimator.
    threshold_ : float
        The threshold value used.

    Examples
    --------
    >>> from nalyst.selection import SelectFromModel
    >>> from nalyst.learners.linear import LassoRegressor
    >>> selector = SelectFromModel(LassoRegressor(alpha=0.1))
    >>> selector.train(X, y)
    >>> X_new = selector.apply(X)
    """

    def __init__(
        self,
        estimator,
        *,
        threshold: Optional[Union[str, float]] = None,
        prefit: bool = False,
        norm_order: int = 1,
        max_features: Optional[int] = None,
        importance_getter: Union[str, callable] = "auto",
    ):
        self.estimator = estimator
        self.threshold = threshold
        self.prefit = prefit
        self.norm_order = norm_order
        self.max_features = max_features
        self.importance_getter = importance_getter

    def _get_feature_importances(self, estimator) -> np.ndarray:
        """Get feature importances from estimator."""
        if callable(self.importance_getter):
            return self.importance_getter(estimator)

        if self.importance_getter == "auto":
            if hasattr(estimator, "feature_importances_"):
                return estimator.feature_importances_
            elif hasattr(estimator, "coef_"):
                coef = estimator.coef_
                if coef.ndim == 1:
                    return np.abs(coef)
                else:
                    return np.linalg.norm(coef, ord=self.norm_order, axis=0)
            else:
                raise ValueError(
                    "Estimator must have feature_importances_ or coef_"
                )
        else:
            return getattr(estimator, self.importance_getter)

    def train(self, X: np.ndarray, y: np.ndarray = None) -> "SelectFromModel":
        """
        Fit the estimator and determine threshold.

        Parameters
        ----------
        X : ndarray of shape (n_samples, n_features)
            Training data.
        y : ndarray of shape (n_samples,), optional
            Target values.

        Returns
        -------
        self : SelectFromModel
            Fitted transformer.
        """
        X = check_array(X)
        self.n_features_in_ = X.shape[1]

        if self.prefit:
            self.estimator_ = self.estimator
        else:
            self.estimator_ = duplicate(self.estimator)
            self.estimator_.train(X, y)

        # Get importances
        importances = self._get_feature_importances(self.estimator_)

        # Determine threshold
        if self.threshold is None:
            threshold = np.mean(importances)
        elif isinstance(self.threshold, str):
            if self.threshold == "mean":
                threshold = np.mean(importances)
            elif self.threshold == "median":
                threshold = np.median(importances)
            elif self.threshold.endswith("*mean"):
                scale = float(self.threshold[:-5])
                threshold = scale * np.mean(importances)
            elif self.threshold.endswith("*median"):
                scale = float(self.threshold[:-7])
                threshold = scale * np.median(importances)
            else:
                raise ValueError(f"Unknown threshold: {self.threshold}")
        else:
            threshold = self.threshold

        self.threshold_ = threshold

        # Get support mask
        mask = importances >= threshold

        # Apply max_features constraint
        if self.max_features is not None:
            if np.sum(mask) > self.max_features:
                indices = np.argsort(importances)[::-1][:self.max_features]
                mask = np.zeros_like(mask)
                mask[indices] = True

        self.support_ = mask

        return self

    def get_support(self, indices: bool = False) -> np.ndarray:
        """Get mask or indices of selected features."""
        check_is_trained(self, "support_")

        if indices:
            return np.where(self.support_)[0]
        return self.support_

    def apply(self, X: np.ndarray) -> np.ndarray:
        """Reduce X to selected features."""
        check_is_trained(self, "support_")
        X = check_array(X)
        return X[:, self.support_]

    def inverse_apply(self, X: np.ndarray) -> np.ndarray:
        """Reverse the transformation."""
        check_is_trained(self, "support_")

        X_r = np.zeros((X.shape[0], self.n_features_in_))
        X_r[:, self.support_] = X

        return X_r
