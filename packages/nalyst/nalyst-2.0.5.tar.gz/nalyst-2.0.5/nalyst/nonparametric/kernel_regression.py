"""
Kernel Regression methods.
"""

from __future__ import annotations

from typing import Optional, Union
import numpy as np


class KernelRegression:
    """
    Base class for kernel regression methods.

    Parameters
    ----------
    kernel : str, default='gaussian'
        Kernel type: 'gaussian', 'epanechnikov', 'triangular'.
    bandwidth : float, optional
        Bandwidth. If None, uses cross-validation.
    """

    def __init__(
        self,
        kernel: str = 'gaussian',
        bandwidth: Optional[float] = None,
    ):
        self.kernel = kernel
        self.bandwidth = bandwidth

    def _kernel_fn(self, u: np.ndarray) -> np.ndarray:
        """Evaluate kernel function."""
        if self.kernel == 'gaussian':
            return np.exp(-0.5 * u ** 2)

        elif self.kernel == 'epanechnikov':
            return np.where(np.abs(u) <= 1, 0.75 * (1 - u ** 2), 0)

        elif self.kernel == 'triangular':
            return np.where(np.abs(u) <= 1, 1 - np.abs(u), 0)

        else:
            return np.exp(-0.5 * u ** 2)

    def _select_bandwidth_cv(
        self,
        X: np.ndarray,
        y: np.ndarray,
        n_bandwidths: int = 20,
    ) -> float:
        """Select bandwidth using leave-one-out cross-validation."""
        # Range of bandwidths
        std = np.std(X)
        n = len(X)

        h_min = 0.1 * std * n ** (-0.2)
        h_max = 2.0 * std * n ** (-0.2)

        bandwidths = np.linspace(h_min, h_max, n_bandwidths)

        best_cv = np.inf
        best_h = bandwidths[len(bandwidths) // 2]

        for h in bandwidths:
            cv_score = 0

            for i in range(n):
                # Leave out i
                X_loo = np.delete(X, i)
                y_loo = np.delete(y, i)

                # Predict i
                u = (X[i] - X_loo) / h
                weights = self._kernel_fn(u)

                if np.sum(weights) > 0:
                    y_pred = np.sum(weights * y_loo) / np.sum(weights)
                else:
                    y_pred = np.mean(y)

                cv_score += (y[i] - y_pred) ** 2

            if cv_score < best_cv:
                best_cv = cv_score
                best_h = h

        return best_h


class NadarayaWatson(KernelRegression):
    """
    Nadaraya-Watson kernel regression.

    Weighted local average: y(x) = sum(K(x-xi) * yi) / sum(K(x-xi))

    Parameters
    ----------
    kernel : str, default='gaussian'
        Kernel type.
    bandwidth : float, optional
        Bandwidth.

    Examples
    --------
    >>> from nalyst.nonparametric import NadarayaWatson
    >>> nw = NadarayaWatson(bandwidth=0.5)
    >>> nw.fit(X, y)
    >>> y_pred = nw.predict(X_new)
    """

    def fit(
        self,
        X: np.ndarray,
        y: np.ndarray,
    ) -> "NadarayaWatson":
        """
        Fit Nadaraya-Watson estimator.

        Parameters
        ----------
        X : ndarray of shape (n_samples,)
            Feature values.
        y : ndarray of shape (n_samples,)
            Target values.

        Returns
        -------
        self
        """
        self.X_ = np.asarray(X).flatten()
        self.y_ = np.asarray(y).flatten()

        if self.bandwidth is None:
            self.bandwidth_ = self._select_bandwidth_cv(self.X_, self.y_)
        else:
            self.bandwidth_ = self.bandwidth

        return self

    def predict(self, X: np.ndarray) -> np.ndarray:
        """
        Predict using Nadaraya-Watson estimator.

        Parameters
        ----------
        X : ndarray
            Points at which to predict.

        Returns
        -------
        y_pred : ndarray
            Predictions.
        """
        X = np.asarray(X).flatten()
        n = len(X)

        y_pred = np.zeros(n)

        for i in range(n):
            u = (X[i] - self.X_) / self.bandwidth_
            weights = self._kernel_fn(u)

            weight_sum = np.sum(weights)

            if weight_sum > 0:
                y_pred[i] = np.sum(weights * self.y_) / weight_sum
            else:
                y_pred[i] = np.mean(self.y_)

        return y_pred

    def train(self, X: np.ndarray, y: np.ndarray) -> "NadarayaWatson":
        """Alias for fit."""
        return self.fit(X, y)

    def infer(self, X: np.ndarray) -> np.ndarray:
        """Alias for predict."""
        return self.predict(X)


class LocalPolynomial(KernelRegression):
    """
    Local polynomial regression.

    Fits weighted polynomial at each point.

    Parameters
    ----------
    degree : int, default=1
        Polynomial degree.
    kernel : str, default='gaussian'
        Kernel type.
    bandwidth : float, optional
        Bandwidth.

    Examples
    --------
    >>> from nalyst.nonparametric import LocalPolynomial
    >>> lp = LocalPolynomial(degree=1, bandwidth=0.5)
    >>> lp.fit(X, y)
    >>> y_pred = lp.predict(X_new)
    """

    def __init__(
        self,
        degree: int = 1,
        kernel: str = 'gaussian',
        bandwidth: Optional[float] = None,
    ):
        super().__init__(kernel, bandwidth)
        self.degree = degree

    def fit(
        self,
        X: np.ndarray,
        y: np.ndarray,
    ) -> "LocalPolynomial":
        """
        Fit local polynomial estimator.

        Parameters
        ----------
        X : ndarray of shape (n_samples,)
            Feature values.
        y : ndarray of shape (n_samples,)
            Target values.

        Returns
        -------
        self
        """
        self.X_ = np.asarray(X).flatten()
        self.y_ = np.asarray(y).flatten()

        if self.bandwidth is None:
            self.bandwidth_ = self._select_bandwidth_cv(self.X_, self.y_)
        else:
            self.bandwidth_ = self.bandwidth

        return self

    def predict(self, X: np.ndarray) -> np.ndarray:
        """
        Predict using local polynomial regression.

        Parameters
        ----------
        X : ndarray
            Points at which to predict.

        Returns
        -------
        y_pred : ndarray
            Predictions.
        """
        X = np.asarray(X).flatten()
        n = len(X)

        y_pred = np.zeros(n)

        for i in range(n):
            # Weights
            u = (X[i] - self.X_) / self.bandwidth_
            weights = self._kernel_fn(u)

            # Design matrix centered at x
            dx = self.X_ - X[i]
            design = np.column_stack([dx ** p for p in range(self.degree + 1)])

            # Weighted least squares
            W = np.diag(weights)

            try:
                XtWX = design.T @ W @ design
                XtWy = design.T @ W @ self.y_
                beta = np.linalg.solve(XtWX + 1e-10 * np.eye(self.degree + 1), XtWy)

                # Prediction is intercept (beta[0])
                y_pred[i] = beta[0]
            except np.linalg.LinAlgError:
                y_pred[i] = np.mean(self.y_)

        return y_pred

    def train(self, X: np.ndarray, y: np.ndarray) -> "LocalPolynomial":
        """Alias for fit."""
        return self.fit(X, y)

    def infer(self, X: np.ndarray) -> np.ndarray:
        """Alias for predict."""
        return self.predict(X)
