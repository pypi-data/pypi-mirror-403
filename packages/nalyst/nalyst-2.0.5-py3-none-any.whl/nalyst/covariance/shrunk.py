"""
Shrunk covariance estimators.
"""

from __future__ import annotations

from typing import Optional

import numpy as np
from scipy import linalg

from nalyst.core.foundation import BaseLearner
from nalyst.core.validation import check_array, check_is_trained


class ShrunkCovariance(BaseLearner):
    """
    Covariance estimator with shrinkage.

    Parameters
    ----------
    store_precision : bool, default=True
        Whether to store the precision matrix.
    assume_centered : bool, default=False
        If True, assume data is centered.
    shrinkage : float, default=0.1
        Shrinkage coefficient.

    Attributes
    ----------
    covariance_ : ndarray
        Shrunk covariance matrix.
    precision_ : ndarray
        Precision matrix.
    shrinkage : float
        Shrinkage coefficient used.

    Examples
    --------
    >>> from nalyst.covariance import ShrunkCovariance
    >>> cov = ShrunkCovariance(shrinkage=0.1)
    >>> cov.train(X)
    """

    def __init__(
        self,
        store_precision: bool = True,
        assume_centered: bool = False,
        shrinkage: float = 0.1,
    ):
        self.store_precision = store_precision
        self.assume_centered = assume_centered
        self.shrinkage = shrinkage

    def train(self, X: np.ndarray, y=None) -> "ShrunkCovariance":
        """Fit the shrunk covariance model."""
        X = check_array(X)
        n_samples, n_features = X.shape

        if self.assume_centered:
            self.location_ = np.zeros(n_features)
        else:
            self.location_ = np.mean(X, axis=0)

        X_centered = X - self.location_
        emp_cov = X_centered.T @ X_centered / n_samples

        # Shrink toward scaled identity
        mu = np.trace(emp_cov) / n_features

        self.covariance_ = (1 - self.shrinkage) * emp_cov + \
                          self.shrinkage * mu * np.eye(n_features)

        if self.store_precision:
            self.precision_ = linalg.pinvh(self.covariance_)

        return self


class LedoitWolf(BaseLearner):
    """
    Ledoit-Wolf shrinkage estimator.

    Optimal shrinkage coefficient estimation using Ledoit-Wolf lemma.

    Parameters
    ----------
    store_precision : bool, default=True
        Whether to store the precision matrix.
    assume_centered : bool, default=False
        If True, assume data is centered.
    block_size : int, default=1000
        Block size for memory-efficient computation.

    Attributes
    ----------
    covariance_ : ndarray
        Estimated covariance matrix.
    shrinkage_ : float
        Optimal shrinkage coefficient.

    Examples
    --------
    >>> from nalyst.covariance import LedoitWolf
    >>> lw = LedoitWolf()
    >>> lw.train(X)
    >>> lw.shrinkage_  # Estimated optimal shrinkage
    """

    def __init__(
        self,
        store_precision: bool = True,
        assume_centered: bool = False,
        block_size: int = 1000,
    ):
        self.store_precision = store_precision
        self.assume_centered = assume_centered
        self.block_size = block_size

    def train(self, X: np.ndarray, y=None) -> "LedoitWolf":
        """Fit the Ledoit-Wolf shrunk covariance model."""
        X = check_array(X)
        n_samples, n_features = X.shape

        if self.assume_centered:
            self.location_ = np.zeros(n_features)
        else:
            self.location_ = np.mean(X, axis=0)

        X_centered = X - self.location_

        # Compute empirical covariance
        emp_cov = X_centered.T @ X_centered / n_samples

        # Compute optimal shrinkage
        self.shrinkage_, self.covariance_ = self._oas(X_centered, emp_cov)

        if self.store_precision:
            self.precision_ = linalg.pinvh(self.covariance_)

        return self

    def _oas(self, X: np.ndarray, emp_cov: np.ndarray):
        """Compute optimal shrinkage using Ledoit-Wolf formula."""
        n_samples, n_features = X.shape

        # Target: scaled identity
        mu = np.trace(emp_cov) / n_features

        # Squared Frobenius norm of centered covariance
        delta = emp_cov - mu * np.eye(n_features)
        delta_sq_sum = np.sum(delta ** 2)

        # Compute cross-product sum
        X_sq = X ** 2
        beta = 0

        for i in range(n_features):
            for j in range(n_features):
                if i == j:
                    beta += np.sum(X_sq[:, i] ** 2) / n_samples
                else:
                    beta += np.sum(X[:, i] ** 2 * X[:, j] ** 2) / n_samples

        beta -= np.sum(emp_cov ** 2)
        beta /= n_samples

        # Optimal shrinkage
        shrinkage = min(1, max(0, beta / delta_sq_sum)) if delta_sq_sum > 0 else 1

        # Shrunk covariance
        cov = (1 - shrinkage) * emp_cov + shrinkage * mu * np.eye(n_features)

        return shrinkage, cov


class OAS(BaseLearner):
    """
    Oracle Approximating Shrinkage estimator.

    Parameters
    ----------
    store_precision : bool, default=True
        Whether to store the precision matrix.
    assume_centered : bool, default=False
        If True, assume data is centered.

    Attributes
    ----------
    covariance_ : ndarray
        Estimated covariance matrix.
    shrinkage_ : float
        Optimal shrinkage coefficient.

    Examples
    --------
    >>> from nalyst.covariance import OAS
    >>> oas = OAS()
    >>> oas.train(X)
    """

    def __init__(
        self,
        store_precision: bool = True,
        assume_centered: bool = False,
    ):
        self.store_precision = store_precision
        self.assume_centered = assume_centered

    def train(self, X: np.ndarray, y=None) -> "OAS":
        """Fit the OAS model."""
        X = check_array(X)
        n_samples, n_features = X.shape

        if self.assume_centered:
            self.location_ = np.zeros(n_features)
        else:
            self.location_ = np.mean(X, axis=0)

        X_centered = X - self.location_

        # Empirical covariance
        emp_cov = X_centered.T @ X_centered / n_samples

        # OAS formula
        mu = np.trace(emp_cov) / n_features

        # Shrinkage factor
        rho = (1 - 2.0 / n_features) * np.sum(emp_cov ** 2) + mu ** 2 * n_features
        rho /= (n_samples + 1 - 2.0 / n_features) * (np.sum(emp_cov ** 2) - mu ** 2 / n_features)

        self.shrinkage_ = min(1, max(0, rho))

        self.covariance_ = (1 - self.shrinkage_) * emp_cov + \
                          self.shrinkage_ * mu * np.eye(n_features)

        if self.store_precision:
            self.precision_ = linalg.pinvh(self.covariance_)

        return self
