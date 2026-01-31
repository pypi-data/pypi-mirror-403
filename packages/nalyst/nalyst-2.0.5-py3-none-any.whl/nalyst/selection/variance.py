"""
Variance Threshold feature selection.
"""

from __future__ import annotations

import numpy as np

from nalyst.core.foundation import BaseLearner, TransformerMixin
from nalyst.core.validation import check_array, check_is_trained


class VarianceThreshold(TransformerMixin, BaseLearner):
    """
    Feature selector that removes low-variance features.

    Parameters
    ----------
    threshold : float, default=0.0
        Features with variance lower than this threshold will be removed.

    Attributes
    ----------
    variances_ : ndarray of shape (n_features,)
        Variances of individual features.
    n_features_in_ : int
        Number of features seen during fit.

    Examples
    --------
    >>> from nalyst.selection import VarianceThreshold
    >>> X = np.array([[0, 0, 1], [0, 1, 0], [1, 0, 0], [0, 1, 1], [0, 1, 0], [0, 1, 1]])
    >>> sel = VarianceThreshold(threshold=0.16)
    >>> X_new = sel.train_apply(X)
    """

    def __init__(self, threshold: float = 0.0):
        self.threshold = threshold

    def train(self, X: np.ndarray, y=None) -> "VarianceThreshold":
        """
        Learn empirical variances from X.

        Parameters
        ----------
        X : ndarray of shape (n_samples, n_features)
            Sample vectors.
        y : ignored

        Returns
        -------
        self : VarianceThreshold
            Fitted transformer.
        """
        X = check_array(X)

        self.variances_ = np.var(X, axis=0)
        self.n_features_in_ = X.shape[1]

        if np.all(~self.get_support()):
            raise ValueError(
                f"No feature in X meets the variance threshold {self.threshold}"
            )

        return self

    def get_support(self, indices: bool = False) -> np.ndarray:
        """
        Get a mask or integer index of selected features.

        Parameters
        ----------
        indices : bool, default=False
            If True, returns indices.

        Returns
        -------
        support : ndarray
            Mask or indices.
        """
        check_is_trained(self, "variances_")
        mask = self.variances_ > self.threshold

        if indices:
            return np.where(mask)[0]
        return mask

    def apply(self, X: np.ndarray) -> np.ndarray:
        """
        Reduce X to selected features.

        Parameters
        ----------
        X : ndarray of shape (n_samples, n_features)
            Input samples.

        Returns
        -------
        X_r : ndarray of shape (n_samples, n_selected_features)
            Input samples with selected features.
        """
        check_is_trained(self, "variances_")
        X = check_array(X)
        return X[:, self.get_support()]

    def inverse_apply(self, X: np.ndarray) -> np.ndarray:
        """
        Reverse the transformation operation.

        Parameters
        ----------
        X : ndarray of shape (n_samples, n_selected_features)
            Input samples.

        Returns
        -------
        X_r : ndarray of shape (n_samples, n_features)
            Zeros in unselected positions.
        """
        check_is_trained(self, "variances_")
        support = self.get_support()

        X_r = np.zeros((X.shape[0], self.n_features_in_))
        X_r[:, support] = X

        return X_r
