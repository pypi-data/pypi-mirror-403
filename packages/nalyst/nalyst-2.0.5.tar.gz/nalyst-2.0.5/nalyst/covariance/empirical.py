"""
Empirical covariance estimator.
"""

from __future__ import annotations

from typing import Optional

import numpy as np
from scipy import linalg

from nalyst.core.foundation import BaseLearner
from nalyst.core.validation import check_array, check_is_trained


class EmpiricalCovariance(BaseLearner):
    """
    Maximum likelihood covariance estimator.

    Parameters
    ----------
    store_precision : bool, default=True
        Whether to store the precision matrix.
    assume_centered : bool, default=False
        If True, assume data is centered.

    Attributes
    ----------
    location_ : ndarray of shape (n_features,)
        Estimated location (mean).
    covariance_ : ndarray of shape (n_features, n_features)
        Estimated covariance matrix.
    precision_ : ndarray of shape (n_features, n_features)
        Estimated precision matrix (inverse of covariance).

    Examples
    --------
    >>> from nalyst.covariance import EmpiricalCovariance
    >>> cov = EmpiricalCovariance()
    >>> cov.train(X)
    >>> cov.covariance_
    """

    def __init__(
        self,
        store_precision: bool = True,
        assume_centered: bool = False,
    ):
        self.store_precision = store_precision
        self.assume_centered = assume_centered

    def train(self, X: np.ndarray, y=None) -> "EmpiricalCovariance":
        """
        Fit the Maximum Likelihood Estimator covariance model.

        Parameters
        ----------
        X : ndarray of shape (n_samples, n_features)
            Training data.
        y : ignored

        Returns
        -------
        self : EmpiricalCovariance
            Fitted estimator.
        """
        X = check_array(X)
        n_samples, n_features = X.shape

        if self.assume_centered:
            self.location_ = np.zeros(n_features)
        else:
            self.location_ = np.mean(X, axis=0)

        X_centered = X - self.location_
        self.covariance_ = X_centered.T @ X_centered / n_samples

        if self.store_precision:
            self.precision_ = linalg.pinvh(self.covariance_)

        return self

    def get_precision(self) -> np.ndarray:
        """
        Getter for the precision matrix.

        Returns
        -------
        precision_ : ndarray of shape (n_features, n_features)
            The precision matrix.
        """
        if self.store_precision:
            return self.precision_
        else:
            return linalg.pinvh(self.covariance_)

    def mahalanobis(self, X: np.ndarray) -> np.ndarray:
        """
        Compute Mahalanobis distance.

        Parameters
        ----------
        X : ndarray of shape (n_samples, n_features)
            Observations.

        Returns
        -------
        dist : ndarray of shape (n_samples,)
            Mahalanobis distances.
        """
        check_is_trained(self, "covariance_")
        X = check_array(X)

        X_centered = X - self.location_
        precision = self.get_precision()

        # d^2 = (x - mu)^T @ precision @ (x - mu)
        dist = np.sum(X_centered @ precision * X_centered, axis=1)

        return dist

    def score(self, X: np.ndarray, y=None) -> float:
        """
        Compute log-likelihood.

        Parameters
        ----------
        X : ndarray of shape (n_samples, n_features)
            Test data.
        y : ignored

        Returns
        -------
        score : float
            Log-likelihood.
        """
        check_is_trained(self, "covariance_")
        X = check_array(X)

        n_samples, n_features = X.shape

        # Log-likelihood = -0.5 * (n * log(det(cov)) + trace(S @ precision))
        log_det = np.linalg.slogdet(self.covariance_)[1]

        X_centered = X - self.location_
        S = X_centered.T @ X_centered / n_samples

        score = -0.5 * (
            n_features * np.log(2 * np.pi) +
            log_det +
            np.trace(S @ self.get_precision())
        )

        return score

    def error_norm(
        self,
        comp_cov: np.ndarray,
        norm: str = "frobenius",
        scaling: bool = True,
        squared: bool = True,
    ) -> float:
        """
        Compute error between estimated and given covariance.

        Parameters
        ----------
        comp_cov : ndarray
            Comparison covariance matrix.
        norm : {"frobenius", "spectral"}, default="frobenius"
            Error norm type.
        scaling : bool, default=True
            Whether to scale by number of features.
        squared : bool, default=True
            Whether to return squared error.

        Returns
        -------
        error : float
            Error value.
        """
        check_is_trained(self, "covariance_")

        diff = self.covariance_ - comp_cov

        if norm == "frobenius":
            error = np.sum(diff ** 2)
        else:  # spectral
            error = np.max(np.abs(linalg.eigvalsh(diff)))
            squared = False  # Spectral norm is not squared

        if scaling:
            error /= self.covariance_.shape[0]

        if not squared and norm == "frobenius":
            error = np.sqrt(error)

        return error
