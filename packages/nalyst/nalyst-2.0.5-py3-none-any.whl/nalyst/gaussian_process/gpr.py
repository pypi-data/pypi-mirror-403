"""
Gaussian Process Regression.
"""

from __future__ import annotations

from typing import Optional, Tuple

import numpy as np
from scipy import linalg

from nalyst.core.foundation import BaseLearner, RegressorMixin
from nalyst.core.validation import check_array, check_is_trained
from nalyst.gaussian_process.kernels import RBF, Kernel


class GaussianProcessRegressor(RegressorMixin, BaseLearner):
    """
    Gaussian Process Regression (GPR).

    Parameters
    ----------
    kernel : Kernel, optional
        The kernel function. Defaults to RBF.
    alpha : float, default=1e-10
        Value added to diagonal for numerical stability.
    optimizer : {"fmin_l_bfgs_b"} or None, default="fmin_l_bfgs_b"
        Optimizer for kernel hyperparameters.
    n_restarts_optimizer : int, default=0
        Number of restarts for optimizer.
    normalize_y : bool, default=False
        Whether to normalize target values.
    random_state : int, optional
        Random seed.

    Attributes
    ----------
    X_train_ : ndarray of shape (n_samples, n_features)
        Feature vectors used in training.
    y_train_ : ndarray of shape (n_samples,)
        Target values in training.
    kernel_ : Kernel
        Kernel used for prediction.
    L_ : ndarray of shape (n_samples, n_samples)
        Lower-triangular Cholesky decomposition.
    alpha_ : ndarray of shape (n_samples,)
        Dual coefficients.
    log_marginal_likelihood_value_ : float
        Log-marginal-likelihood of training data.

    Examples
    --------
    >>> from nalyst.gaussian_process import GaussianProcessRegressor, RBF
    >>> kernel = RBF(length_scale=1.0)
    >>> gpr = GaussianProcessRegressor(kernel=kernel)
    >>> gpr.train(X, y)
    >>> y_pred, y_std = gpr.infer(X_test, return_std=True)
    """

    def __init__(
        self,
        kernel: Optional[Kernel] = None,
        *,
        alpha: float = 1e-10,
        optimizer: Optional[str] = "fmin_l_bfgs_b",
        n_restarts_optimizer: int = 0,
        normalize_y: bool = False,
        random_state: Optional[int] = None,
    ):
        self.kernel = kernel
        self.alpha = alpha
        self.optimizer = optimizer
        self.n_restarts_optimizer = n_restarts_optimizer
        self.normalize_y = normalize_y
        self.random_state = random_state

    def train(self, X: np.ndarray, y: np.ndarray) -> "GaussianProcessRegressor":
        """
        Fit Gaussian process regression model.

        Parameters
        ----------
        X : ndarray of shape (n_samples, n_features)
            Feature vectors.
        y : ndarray of shape (n_samples,) or (n_samples, n_targets)
            Target values.

        Returns
        -------
        self : GaussianProcessRegressor
            Fitted estimator.
        """
        X = check_array(X)
        y = np.atleast_1d(y)

        if self.random_state is not None:
            np.random.seed(self.random_state)

        self.kernel_ = self.kernel if self.kernel is not None else RBF()

        # Normalize y
        if self.normalize_y:
            self._y_train_mean = np.mean(y, axis=0)
            self._y_train_std = np.std(y, axis=0)
            self._y_train_std = np.where(self._y_train_std == 0, 1, self._y_train_std)
            y = (y - self._y_train_mean) / self._y_train_std
        else:
            self._y_train_mean = 0
            self._y_train_std = 1

        self.X_train_ = X
        self.y_train_ = y

        # Compute kernel matrix
        K = self.kernel_(X)
        K += self.alpha * np.eye(len(X))

        # Cholesky decomposition
        try:
            self.L_ = linalg.cholesky(K, lower=True)
        except linalg.LinAlgError:
            # Add more regularization
            K += 1e-6 * np.eye(len(X))
            self.L_ = linalg.cholesky(K, lower=True)

        # Compute alpha
        self.alpha_ = linalg.cho_solve((self.L_, True), y)

        # Compute log marginal likelihood
        self.log_marginal_likelihood_value_ = self._log_marginal_likelihood()

        return self

    def _log_marginal_likelihood(self) -> float:
        """Compute log marginal likelihood."""
        n = len(self.y_train_)

        # -0.5 * y^T @ alpha - sum(log(diag(L))) - n/2 * log(2*pi)
        log_likelihood = -0.5 * np.dot(self.y_train_.T, self.alpha_)
        log_likelihood -= np.sum(np.log(np.diag(self.L_)))
        log_likelihood -= 0.5 * n * np.log(2 * np.pi)

        return float(log_likelihood)

    def infer(
        self, X: np.ndarray, return_std: bool = False, return_cov: bool = False
    ) -> np.ndarray:
        """
        Predict using the Gaussian process regression model.

        Parameters
        ----------
        X : ndarray of shape (n_samples, n_features)
            Query points.
        return_std : bool, default=False
            If True, return standard deviation.
        return_cov : bool, default=False
            If True, return covariance.

        Returns
        -------
        y_mean : ndarray of shape (n_samples,)
            Mean of predictive distribution.
        y_std : ndarray of shape (n_samples,), optional
            Standard deviation.
        y_cov : ndarray of shape (n_samples, n_samples), optional
            Covariance matrix.
        """
        check_is_trained(self, "X_train_")
        X = check_array(X)

        # Compute cross-covariance
        K_trans = self.kernel_(X, self.X_train_)

        # Mean prediction
        y_mean = K_trans @ self.alpha_

        # Denormalize
        y_mean = y_mean * self._y_train_std + self._y_train_mean

        if return_std or return_cov:
            # Compute v = L^-1 @ K_trans.T
            v = linalg.solve_triangular(self.L_, K_trans.T, lower=True)

            # Prior variance
            y_var = self.kernel_.diag(X)

            # Posterior variance
            y_var -= np.sum(v ** 2, axis=0)

            # Handle negative variance from numerical errors
            y_var = np.maximum(y_var, 0)

            if return_std:
                y_std = np.sqrt(y_var) * self._y_train_std
                if return_cov:
                    # Posterior covariance
                    y_cov = self.kernel_(X) - v.T @ v
                    y_cov *= self._y_train_std ** 2
                    return y_mean, y_std, y_cov
                return y_mean, y_std
            else:
                y_cov = self.kernel_(X) - v.T @ v
                y_cov *= self._y_train_std ** 2
                return y_mean, y_cov

        return y_mean

    def sample_y(
        self, X: np.ndarray, n_samples: int = 1, random_state: Optional[int] = None
    ) -> np.ndarray:
        """
        Draw samples from the Gaussian process.

        Parameters
        ----------
        X : ndarray of shape (n_samples, n_features)
            Query points.
        n_samples : int, default=1
            Number of samples to draw.
        random_state : int, optional
            Random seed.

        Returns
        -------
        y_samples : ndarray of shape (n_samples, n_draws)
            Samples from the posterior distribution.
        """
        if random_state is not None:
            np.random.seed(random_state)

        y_mean, y_cov = self.infer(X, return_cov=True)

        # Sample from multivariate normal
        samples = np.random.multivariate_normal(y_mean, y_cov, n_samples).T

        return samples

    def score(self, X: np.ndarray, y: np.ndarray) -> float:
        """
        Return the coefficient of determination R^2.

        Parameters
        ----------
        X : ndarray of shape (n_samples, n_features)
            Test samples.
        y : ndarray of shape (n_samples,)
            True values.

        Returns
        -------
        score : float
            R^2 score.
        """
        y_pred = self.infer(X)
        ss_res = np.sum((y - y_pred) ** 2)
        ss_tot = np.sum((y - np.mean(y)) ** 2)
        return 1 - ss_res / ss_tot
