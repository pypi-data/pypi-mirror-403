"""
Base classes for linear models.
"""

from __future__ import annotations

from abc import abstractmethod
from typing import Any, Optional, Union

import numpy as np
from scipy import sparse

from nalyst.core.foundation import BaseLearner
from nalyst.core.validation import check_array, check_X_y


class LinearModel(BaseLearner):
    """
    Base class for linear models.

    Provides common functionality for models of the form:
        y = X @ coef_ + intercept_

    Attributes
    ----------
    coef_ : ndarray of shape (n_features,) or (n_targets, n_features)
        Coefficients of the linear model.
    intercept_ : float or ndarray of shape (n_targets,)
        Independent term in the model.
    n_features_in_ : int
        Number of features seen during training.
    feature_names_in_ : ndarray of shape (n_features,), optional
        Feature names seen during training.
    """

    def _decision_function(self, X: np.ndarray) -> np.ndarray:
        """
        Compute the linear decision function.

        Parameters
        ----------
        X : array-like of shape (n_samples, n_features)
            Input samples.

        Returns
        -------
        scores : ndarray of shape (n_samples,) or (n_samples, n_targets)
            Raw decision values.
        """
        from nalyst.core.validation import check_is_trained
        check_is_trained(self)

        X = check_array(X, accept_sparse=["csr", "csc", "coo"])

        scores = X @ self.coef_.T
        if hasattr(self, "intercept_"):
            scores = scores + self.intercept_

        return scores

    def _set_intercept(
        self,
        X_offset: np.ndarray,
        y_offset: np.ndarray,
        X_scale: np.ndarray,
    ) -> None:
        """
        Set intercept after fitting on centered data.

        Parameters
        ----------
        X_offset : ndarray
            Mean of X used for centering.
        y_offset : ndarray
            Mean of y used for centering.
        X_scale : ndarray
            Standard deviation of X used for scaling.
        """
        if self.fit_intercept:
            self.coef_ = self.coef_ / X_scale
            self.intercept_ = y_offset - np.dot(X_offset, self.coef_.T)
        else:
            self.intercept_ = 0.0

    @staticmethod
    def _preprocess_data(
        X: np.ndarray,
        y: np.ndarray,
        *,
        fit_intercept: bool = True,
        copy: bool = True,
        sample_weight: Optional[np.ndarray] = None,
    ) -> tuple:
        """
        Center and scale data for fitting.

        Parameters
        ----------
        X : ndarray of shape (n_samples, n_features)
            Training data.
        y : ndarray of shape (n_samples,) or (n_samples, n_targets)
            Target values.
        fit_intercept : bool
            Whether to center data.
        copy : bool
            Whether to copy data.
        sample_weight : ndarray, optional
            Sample weights.

        Returns
        -------
        X : ndarray
            Preprocessed X.
        y : ndarray
            Preprocessed y.
        X_offset : ndarray
            Mean of X.
        y_offset : float or ndarray
            Mean of y.
        X_scale : ndarray
            Scale factors for X.
        """
        if copy:
            X = X.copy()
            y = y.copy()

        if fit_intercept:
            if sample_weight is not None:
                sw = sample_weight / np.sum(sample_weight)
                X_offset = np.average(X, axis=0, weights=sw)
                y_offset = np.average(y, axis=0, weights=sw)
            else:
                X_offset = np.mean(X, axis=0)
                y_offset = np.mean(y, axis=0) if y.ndim > 1 else np.mean(y)

            X = X - X_offset
            y = y - y_offset
        else:
            X_offset = np.zeros(X.shape[1], dtype=X.dtype)
            y_offset = 0.0 if y.ndim == 1 else np.zeros(y.shape[1], dtype=y.dtype)

        X_scale = np.ones(X.shape[1], dtype=X.dtype)

        return X, y, X_offset, y_offset, X_scale


def _rescale_data(
    X: np.ndarray,
    y: np.ndarray,
    sample_weight: np.ndarray,
) -> tuple:
    """
    Rescale data by square root of sample weights.

    Parameters
    ----------
    X : ndarray
        Feature matrix.
    y : ndarray
        Target values.
    sample_weight : ndarray
        Sample weights.

    Returns
    -------
    X_rescaled : ndarray
    y_rescaled : ndarray
    sqrt_sw : ndarray
        Square root of sample weights.
    """
    sqrt_sw = np.sqrt(sample_weight)

    if sparse.issparse(X):
        X = X.multiply(sqrt_sw[:, np.newaxis])
    else:
        X = X * sqrt_sw[:, np.newaxis]

    y = y * sqrt_sw

    return X, y, sqrt_sw
