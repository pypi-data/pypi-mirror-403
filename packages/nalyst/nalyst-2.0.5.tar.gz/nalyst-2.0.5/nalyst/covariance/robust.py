"""
Robust covariance estimators.
"""

from __future__ import annotations

from typing import Optional

import numpy as np
from scipy import linalg

from nalyst.core.foundation import BaseLearner
from nalyst.core.validation import check_array, check_is_trained


class MinCovDet(BaseLearner):
    """
    Minimum Covariance Determinant estimator.

    Robust estimator of covariance for outlier detection.

    Parameters
    ----------
    store_precision : bool, default=True
        Whether to store the precision matrix.
    assume_centered : bool, default=False
        If True, assume data is centered.
    support_fraction : float, optional
        Proportion of points for robust estimation.
    random_state : int, optional
        Random seed.

    Attributes
    ----------
    location_ : ndarray
        Robust mean estimate.
    covariance_ : ndarray
        Robust covariance estimate.
    support_ : ndarray
        Mask of inliers.

    Examples
    --------
    >>> from nalyst.covariance import MinCovDet
    >>> mcd = MinCovDet()
    >>> mcd.train(X)
    >>> mcd.mahalanobis(X)  # Robust Mahalanobis distances
    """

    def __init__(
        self,
        store_precision: bool = True,
        assume_centered: bool = False,
        support_fraction: Optional[float] = None,
        random_state: Optional[int] = None,
    ):
        self.store_precision = store_precision
        self.assume_centered = assume_centered
        self.support_fraction = support_fraction
        self.random_state = random_state

    def train(self, X: np.ndarray, y=None) -> "MinCovDet":
        """
        Fit the Minimum Covariance Determinant model.

        Parameters
        ----------
        X : ndarray of shape (n_samples, n_features)
            Training data.
        y : ignored

        Returns
        -------
        self : MinCovDet
            Fitted estimator.
        """
        X = check_array(X)
        n_samples, n_features = X.shape

        if self.random_state is not None:
            np.random.seed(self.random_state)

        # Determine support fraction
        if self.support_fraction is None:
            n_support = int(np.ceil(0.5 * (n_samples + n_features + 1)))
        else:
            n_support = int(n_samples * self.support_fraction)

        # Fast MCD algorithm (simplified)
        best_det = float('inf')
        best_location = None
        best_covariance = None
        best_support = None

        # Multiple random starts
        for _ in range(10):
            # Random initial subset
            indices = np.random.choice(n_samples, n_features + 1, replace=False)

            for _ in range(20):  # C-step iterations
                X_subset = X[indices]

                if self.assume_centered:
                    location = np.zeros(n_features)
                else:
                    location = np.mean(X_subset, axis=0)

                centered = X_subset - location
                covariance = centered.T @ centered / len(centered)

                # Regularize if needed
                covariance += 1e-6 * np.eye(n_features)

                # Compute Mahalanobis distances
                precision = linalg.pinvh(covariance)
                centered_all = X - location
                distances = np.sum(centered_all @ precision * centered_all, axis=1)

                # Select closest points
                new_indices = np.argsort(distances)[:n_support]

                if np.array_equal(new_indices, indices):
                    break

                indices = new_indices

            # Check determinant
            det = np.linalg.det(covariance)
            if det < best_det and det > 0:
                best_det = det
                best_location = location
                best_covariance = covariance
                best_support = indices

        self.location_ = best_location
        self.covariance_ = best_covariance
        self.support_ = np.zeros(n_samples, dtype=bool)
        self.support_[best_support] = True

        if self.store_precision:
            self.precision_ = linalg.pinvh(self.covariance_)

        return self

    def mahalanobis(self, X: np.ndarray) -> np.ndarray:
        """Compute Mahalanobis distances."""
        check_is_trained(self, "covariance_")
        X = check_array(X)

        centered = X - self.location_
        precision = linalg.pinvh(self.covariance_)

        return np.sum(centered @ precision * centered, axis=1)


class EllipticEnvelope(MinCovDet):
    """
    Outlier detection using an elliptic envelope.

    Parameters
    ----------
    store_precision : bool, default=True
        Whether to store the precision matrix.
    assume_centered : bool, default=False
        If True, assume data is centered.
    support_fraction : float, optional
        Proportion of points for robust estimation.
    contamination : float, default=0.1
        Expected proportion of outliers.
    random_state : int, optional
        Random seed.

    Attributes
    ----------
    offset_ : float
        Threshold for outlier detection.

    Examples
    --------
    >>> from nalyst.covariance import EllipticEnvelope
    >>> ee = EllipticEnvelope(contamination=0.1)
    >>> ee.train(X)
    >>> predictions = ee.infer(X)  # -1 for outliers
    """

    def __init__(
        self,
        store_precision: bool = True,
        assume_centered: bool = False,
        support_fraction: Optional[float] = None,
        contamination: float = 0.1,
        random_state: Optional[int] = None,
    ):
        super().__init__(
            store_precision=store_precision,
            assume_centered=assume_centered,
            support_fraction=support_fraction,
            random_state=random_state,
        )
        self.contamination = contamination

    def train(self, X: np.ndarray, y=None) -> "EllipticEnvelope":
        """Fit the elliptic envelope."""
        super().train(X, y)

        # Compute threshold
        distances = self.mahalanobis(X)
        self.offset_ = np.percentile(distances, 100 * (1 - self.contamination))

        return self

    def infer(self, X: np.ndarray) -> np.ndarray:
        """
        Predict if samples are outliers.

        Parameters
        ----------
        X : ndarray of shape (n_samples, n_features)
            Input data.

        Returns
        -------
        y_pred : ndarray of shape (n_samples,)
            +1 for inliers, -1 for outliers.
        """
        scores = self.decision_function(X)
        return np.where(scores >= 0, 1, -1)

    def decision_function(self, X: np.ndarray) -> np.ndarray:
        """
        Compute decision function.

        Parameters
        ----------
        X : ndarray of shape (n_samples, n_features)
            Input data.

        Returns
        -------
        scores : ndarray of shape (n_samples,)
            Negative = outlier.
        """
        check_is_trained(self, "offset_")
        distances = self.mahalanobis(X)
        return self.offset_ - distances
