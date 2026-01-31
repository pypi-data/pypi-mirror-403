"""
Factor Analysis.
"""

from __future__ import annotations

from typing import Optional, Literal

import numpy as np
from scipy import linalg

from nalyst.core.foundation import BaseLearner, TransformerMixin
from nalyst.core.validation import check_array, check_is_trained


class FactorAnalysis(TransformerMixin, BaseLearner):
    """
    Factor Analysis.

    A simple linear generative model with Gaussian latent variables.

    Parameters
    ----------
    n_components : int, optional
        Dimensionality of latent space. If None, n_features.
    tol : float, default=1e-2
        Stopping tolerance for log-likelihood increase.
    max_iter : int, default=1000
        Maximum number of iterations.
    noise_variance_init : ndarray, optional
        Initial noise variance.
    svd_method : {"lapack", "randomized"}, default="randomized"
        SVD method.
    random_state : int, optional
        Random seed.

    Attributes
    ----------
    components_ : ndarray of shape (n_components, n_features)
        Factor loadings.
    noise_variance_ : ndarray of shape (n_features,)
        Estimated noise variance per feature.
    mean_ : ndarray of shape (n_features,)
        Per-feature empirical mean.
    n_iter_ : int
        Number of iterations.

    Examples
    --------
    >>> from nalyst.reduction import FactorAnalysis
    >>> X = np.random.randn(100, 10)
    >>> fa = FactorAnalysis(n_components=3)
    >>> fa.train(X)
    FactorAnalysis(n_components=3)
    >>> X_transformed = fa.apply(X)
    """

    def __init__(
        self,
        n_components: Optional[int] = None,
        *,
        tol: float = 1e-2,
        max_iter: int = 1000,
        noise_variance_init: Optional[np.ndarray] = None,
        svd_method: Literal["lapack", "randomized"] = "randomized",
        random_state: Optional[int] = None,
    ):
        self.n_components = n_components
        self.tol = tol
        self.max_iter = max_iter
        self.noise_variance_init = noise_variance_init
        self.svd_method = svd_method
        self.random_state = random_state

    def train(self, X: np.ndarray, y=None) -> "FactorAnalysis":
        """
        Fit the Factor Analysis model with X.

        Parameters
        ----------
        X : ndarray of shape (n_samples, n_features)
            Training data.
        y : ignored

        Returns
        -------
        self : FactorAnalysis
            Fitted transformer.
        """
        X = check_array(X)
        n_samples, n_features = X.shape

        n_components = self.n_components or n_features

        if self.random_state is not None:
            np.random.seed(self.random_state)

        # Center data
        self.mean_ = np.mean(X, axis=0)
        X_centered = X - self.mean_

        # Initialize
        var = np.var(X_centered, axis=0)

        if self.noise_variance_init is not None:
            psi = self.noise_variance_init.copy()
        else:
            psi = np.full(n_features, var.mean())

        # Initialize components using SVD
        U, S, Vt = linalg.svd(X_centered, full_matrices=False)
        W = Vt[:n_components].T * S[:n_components]

        loglike = []

        for n_iter in range(self.max_iter):
            # E-step
            sqrt_psi = np.sqrt(psi) + 1e-10
            W_scaled = W / sqrt_psi[:, np.newaxis]

            # Compute covariance of latent factors
            cov_z = linalg.inv(np.eye(n_components) + np.dot(W_scaled.T, W_scaled))

            # Expected latent factors
            X_scaled = X_centered / sqrt_psi
            Ez = np.dot(np.dot(X_scaled, W_scaled), cov_z)

            # M-step
            # Update W
            A = np.dot(Ez.T, Ez) + n_samples * cov_z
            B = np.dot(Ez.T, X_centered)
            W = linalg.solve(A, B).T

            # Update psi
            psi = var - np.sum(W * np.dot(B.T, linalg.inv(A)), axis=1)
            psi = np.maximum(psi, 1e-10)

            # Compute log-likelihood
            sqrt_psi = np.sqrt(psi) + 1e-10
            W_scaled = W / sqrt_psi[:, np.newaxis]

            cov = np.dot(W_scaled.T, W_scaled) + np.eye(n_components)
            sign, logdet = np.linalg.slogdet(cov)

            precision = linalg.inv(cov)
            X_scaled = X_centered / sqrt_psi
            log_like = -0.5 * (
                n_features * np.log(2 * np.pi) +
                logdet +
                np.sum(np.log(psi)) +
                np.sum(np.dot(X_scaled, precision) * X_scaled) / n_samples
            )
            loglike.append(log_like)

            if n_iter > 0 and abs(loglike[-1] - loglike[-2]) < self.tol:
                break

        self.components_ = W.T
        self.noise_variance_ = psi
        self.n_iter_ = n_iter + 1
        self.loglike_ = loglike

        return self

    def apply(self, X: np.ndarray) -> np.ndarray:
        """
        Apply dimensionality reduction to X.

        Parameters
        ----------
        X : ndarray of shape (n_samples, n_features)
            Data to transform.

        Returns
        -------
        X_new : ndarray of shape (n_samples, n_components)
            Transformed data.
        """
        check_is_trained(self, "components_")
        X = check_array(X)

        X_centered = X - self.mean_

        # Compute posterior mean of latent factors
        Ih = np.eye(self.components_.shape[0])
        W = self.components_.T
        psi = self.noise_variance_

        precision = linalg.inv(Ih + np.dot(W.T / psi, W))
        return np.dot(np.dot(X_centered / psi, W), precision)

    def get_covariance(self) -> np.ndarray:
        """
        Compute data covariance with the Factor Analysis model.

        Returns
        -------
        cov : ndarray of shape (n_features, n_features)
            Estimated covariance.
        """
        check_is_trained(self, "components_")

        W = self.components_.T
        return np.dot(W, W.T) + np.diag(self.noise_variance_)

    def get_precision(self) -> np.ndarray:
        """
        Compute data precision matrix.

        Returns
        -------
        precision : ndarray of shape (n_features, n_features)
            Estimated precision.
        """
        check_is_trained(self, "components_")

        return linalg.inv(self.get_covariance())

    def score_samples(self, X: np.ndarray) -> np.ndarray:
        """
        Compute the log-likelihood of each sample.

        Parameters
        ----------
        X : ndarray of shape (n_samples, n_features)
            Samples.

        Returns
        -------
        ll : ndarray of shape (n_samples,)
            Log-likelihood of each sample.
        """
        check_is_trained(self, "components_")
        X = check_array(X)

        X_centered = X - self.mean_
        n_features = X.shape[1]

        cov = self.get_covariance()
        sign, logdet = np.linalg.slogdet(cov)
        precision = self.get_precision()

        log_like = -0.5 * (
            n_features * np.log(2 * np.pi) +
            logdet +
            np.sum(np.dot(X_centered, precision) * X_centered, axis=1)
        )

        return log_like

    def score(self, X: np.ndarray, y=None) -> float:
        """
        Compute average log-likelihood.

        Parameters
        ----------
        X : ndarray of shape (n_samples, n_features)
            Samples.
        y : ignored

        Returns
        -------
        ll : float
            Average log-likelihood.
        """
        return float(np.mean(self.score_samples(X)))
