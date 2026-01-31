"""
Robust Linear Models.
"""

from __future__ import annotations

from typing import Optional, Dict, Any
import numpy as np


class RobustLinearModel:
    """
    Robust Linear Model using iteratively reweighted least squares (IRLS).

    Uses M-estimation to fit a linear model that is robust to outliers.

    Parameters
    ----------
    m_estimator : str or object, default='huber'
        M-estimator for computing weights: 'huber', 'tukey', 'andrew'.
    c : float, default=1.345
        Tuning constant for M-estimator.
    max_iter : int, default=50
        Maximum IRLS iterations.
    tol : float, default=1e-4
        Convergence tolerance.

    Attributes
    ----------
    coef_ : ndarray of shape (n_features,)
        Coefficients.
    intercept_ : float
        Intercept.
    scale_ : float
        Estimated scale of residuals.
    weights_ : ndarray
        Final weights.

    Examples
    --------
    >>> from nalyst.robust import RobustLinearModel
    >>> rlm = RobustLinearModel(m_estimator='huber')
    >>> rlm.train(X, y)
    >>> predictions = rlm.infer(X_new)
    """

    def __init__(
        self,
        m_estimator: str = 'huber',
        c: float = 1.345,
        max_iter: int = 50,
        tol: float = 1e-4,
    ):
        self.m_estimator = m_estimator
        self.c = c
        self.max_iter = max_iter
        self.tol = tol

    def train(self, X: np.ndarray, y: np.ndarray) -> "RobustLinearModel":
        """
        Fit robust linear model.

        Parameters
        ----------
        X : ndarray of shape (n_samples, n_features)
            Features.
        y : ndarray of shape (n_samples,)
            Target.

        Returns
        -------
        self
        """
        X = np.asarray(X)
        y = np.asarray(y).flatten()

        n_samples, n_features = X.shape

        # Add intercept column
        X_design = np.column_stack([np.ones(n_samples), X])

        # Initial OLS estimate
        beta = np.linalg.lstsq(X_design, y, rcond=None)[0]

        # Get weight function
        weight_fn = self._get_weight_function()

        for iteration in range(self.max_iter):
            # Compute residuals
            residuals = y - X_design @ beta

            # Estimate scale (MAD)
            scale = 1.4826 * np.median(np.abs(residuals - np.median(residuals)))
            scale = max(scale, 1e-10)
            self.scale_ = scale

            # Standardized residuals
            u = residuals / scale

            # Compute weights
            weights = weight_fn(u)

            # Weighted least squares
            W = np.diag(weights)
            try:
                XtWX = X_design.T @ W @ X_design
                XtWy = X_design.T @ W @ y
                beta_new = np.linalg.solve(XtWX + 1e-8 * np.eye(len(beta)), XtWy)
            except np.linalg.LinAlgError:
                break

            # Check convergence
            if np.max(np.abs(beta_new - beta)) < self.tol:
                beta = beta_new
                break

            beta = beta_new

        self.intercept_ = beta[0]
        self.coef_ = beta[1:]
        self.weights_ = weights

        return self

    def _get_weight_function(self):
        """Get weight function for M-estimator."""
        c = self.c

        if self.m_estimator == 'huber':
            def weights(u):
                return np.where(np.abs(u) <= c, 1.0, c / np.abs(u))

        elif self.m_estimator == 'tukey':
            def weights(u):
                mask = np.abs(u) <= c
                w = np.zeros_like(u)
                w[mask] = (1 - (u[mask] / c) ** 2) ** 2
                return w

        elif self.m_estimator == 'andrew':
            def weights(u):
                mask = np.abs(u) <= np.pi * c
                w = np.zeros_like(u)
                w[mask] = np.sin(u[mask] / c) / (u[mask] / c + 1e-10)
                return w

        else:
            # Default to Huber
            def weights(u):
                return np.where(np.abs(u) <= c, 1.0, c / np.abs(u))

        return weights

    def infer(self, X: np.ndarray) -> np.ndarray:
        """
        Make predictions.

        Parameters
        ----------
        X : ndarray of shape (n_samples, n_features)
            Features.

        Returns
        -------
        predictions : ndarray of shape (n_samples,)
        """
        X = np.asarray(X)
        return X @ self.coef_ + self.intercept_

    def summary(self) -> Dict[str, Any]:
        """
        Get model summary.

        Returns
        -------
        summary : dict
            Model statistics.
        """
        return {
            'coefficients': self.coef_,
            'intercept': self.intercept_,
            'scale': self.scale_,
            'm_estimator': self.m_estimator,
            'tuning_constant': self.c,
        }


class HuberRegressor:
    """
    Huber Regression.

    Linear regression with Huber loss, robust to outliers.

    Parameters
    ----------
    epsilon : float, default=1.35
        Threshold at which to switch between L1 and L2 loss.
    max_iter : int, default=100
        Maximum iterations.
    alpha : float, default=0.0001
        Regularization parameter.
    tol : float, default=1e-5
        Convergence tolerance.

    Examples
    --------
    >>> from nalyst.robust import HuberRegressor
    >>> huber = HuberRegressor(epsilon=1.35)
    >>> huber.train(X, y)
    """

    def __init__(
        self,
        epsilon: float = 1.35,
        max_iter: int = 100,
        alpha: float = 0.0001,
        tol: float = 1e-5,
    ):
        self.epsilon = epsilon
        self.max_iter = max_iter
        self.alpha = alpha
        self.tol = tol

    def train(self, X: np.ndarray, y: np.ndarray) -> "HuberRegressor":
        """Fit Huber regressor."""
        X = np.asarray(X)
        y = np.asarray(y).flatten()

        n_samples, n_features = X.shape

        # Add intercept
        X_design = np.column_stack([np.ones(n_samples), X])

        # Initialize with OLS
        beta = np.linalg.lstsq(X_design, y, rcond=None)[0]

        # Initial scale
        residuals = y - X_design @ beta
        scale = np.std(residuals) + 1e-10

        for _ in range(self.max_iter):
            # Compute weights based on Huber loss
            z = residuals / scale
            mask = np.abs(z) <= self.epsilon

            weights = np.ones(n_samples)
            weights[~mask] = self.epsilon / np.abs(z[~mask])

            # Weighted least squares with regularization
            W = np.diag(weights)
            reg = self.alpha * np.eye(len(beta))
            reg[0, 0] = 0  # Don't regularize intercept

            XtWX = X_design.T @ W @ X_design + reg
            XtWy = X_design.T @ W @ y

            beta_new = np.linalg.solve(XtWX, XtWy)

            # Update residuals and scale
            residuals_new = y - X_design @ beta_new

            # Update scale using Huber criterion
            z_new = residuals_new / scale
            mask_new = np.abs(z_new) <= self.epsilon

            scale_new = np.sqrt(np.mean(
                np.where(mask_new, residuals_new ** 2,
                        2 * self.epsilon * scale * np.abs(residuals_new) -
                        (self.epsilon * scale) ** 2)
            ))
            scale_new = max(scale_new, 1e-10)

            # Check convergence
            if np.max(np.abs(beta_new - beta)) < self.tol:
                beta = beta_new
                break

            beta = beta_new
            residuals = residuals_new
            scale = scale_new

        self.intercept_ = beta[0]
        self.coef_ = beta[1:]
        self.scale_ = scale

        return self

    def infer(self, X: np.ndarray) -> np.ndarray:
        """Make predictions."""
        X = np.asarray(X)
        return X @ self.coef_ + self.intercept_


class TheilSenRegressor:
    """
    Theil-Sen Regressor.

    Robust regression based on median of pairwise slopes.

    Parameters
    ----------
    max_subpopulation : int, default=10000
        Maximum number of slope samples to use.
    n_subsamples : int, optional
        Number of samples to use for fitting.
    random_state : int, optional
        Random seed.

    Examples
    --------
    >>> from nalyst.robust import TheilSenRegressor
    >>> ts = TheilSenRegressor()
    >>> ts.train(X, y)
    """

    def __init__(
        self,
        max_subpopulation: int = 10000,
        n_subsamples: Optional[int] = None,
        random_state: Optional[int] = None,
    ):
        self.max_subpopulation = max_subpopulation
        self.n_subsamples = n_subsamples
        self.random_state = random_state

    def train(self, X: np.ndarray, y: np.ndarray) -> "TheilSenRegressor":
        """Fit Theil-Sen regressor."""
        X = np.asarray(X)
        y = np.asarray(y).flatten()

        if self.random_state is not None:
            np.random.seed(self.random_state)

        n_samples, n_features = X.shape

        # For univariate case, compute median of pairwise slopes
        if n_features == 1:
            x = X.flatten()
            slopes = []

            n_pairs = n_samples * (n_samples - 1) // 2

            if n_pairs <= self.max_subpopulation:
                # Compute all pairs
                for i in range(n_samples):
                    for j in range(i + 1, n_samples):
                        if x[i] != x[j]:
                            slopes.append((y[j] - y[i]) / (x[j] - x[i]))
            else:
                # Sample pairs
                for _ in range(self.max_subpopulation):
                    i, j = np.random.choice(n_samples, 2, replace=False)
                    if x[i] != x[j]:
                        slopes.append((y[j] - y[i]) / (x[j] - x[i]))

            slope = np.median(slopes) if slopes else 0
            intercept = np.median(y - slope * x)

            self.coef_ = np.array([slope])
            self.intercept_ = intercept

        else:
            # Multivariate: use subsampling approach
            n_subsamples = self.n_subsamples or n_features + 1

            coefs = []
            intercepts = []

            n_iter = min(self.max_subpopulation, n_samples * 10)

            for _ in range(n_iter):
                # Sample n_subsamples points
                idx = np.random.choice(n_samples, min(n_subsamples, n_samples), replace=False)
                X_sub = X[idx]
                y_sub = y[idx]

                try:
                    # Fit OLS on subsample
                    X_design = np.column_stack([np.ones(len(idx)), X_sub])
                    beta = np.linalg.lstsq(X_design, y_sub, rcond=None)[0]
                    intercepts.append(beta[0])
                    coefs.append(beta[1:])
                except np.linalg.LinAlgError:
                    continue

            # Take spatial median (componentwise median)
            self.coef_ = np.median(coefs, axis=0) if coefs else np.zeros(n_features)
            self.intercept_ = np.median(intercepts) if intercepts else 0

        return self

    def infer(self, X: np.ndarray) -> np.ndarray:
        """Make predictions."""
        X = np.asarray(X)
        return X @ self.coef_ + self.intercept_


class RANSACRegressor:
    """
    RANSAC (Random Sample Consensus) Regressor.

    Fits model on random inlier subsets and selects best model.

    Parameters
    ----------
    min_samples : int or float, default=0.5
        Minimum samples for fitting. Float for fraction.
    residual_threshold : float, optional
        Maximum residual to be considered inlier.
    max_trials : int, default=100
        Maximum RANSAC iterations.
    random_state : int, optional
        Random seed.

    Attributes
    ----------
    coef_ : ndarray
        Coefficients.
    intercept_ : float
        Intercept.
    inlier_mask_ : ndarray
        Boolean mask of inliers.

    Examples
    --------
    >>> from nalyst.robust import RANSACRegressor
    >>> ransac = RANSACRegressor(residual_threshold=5.0)
    >>> ransac.train(X, y)
    """

    def __init__(
        self,
        min_samples: float = 0.5,
        residual_threshold: Optional[float] = None,
        max_trials: int = 100,
        random_state: Optional[int] = None,
    ):
        self.min_samples = min_samples
        self.residual_threshold = residual_threshold
        self.max_trials = max_trials
        self.random_state = random_state

    def train(self, X: np.ndarray, y: np.ndarray) -> "RANSACRegressor":
        """Fit RANSAC regressor."""
        X = np.asarray(X)
        y = np.asarray(y).flatten()

        if self.random_state is not None:
            np.random.seed(self.random_state)

        n_samples, n_features = X.shape

        # Determine min_samples
        if isinstance(self.min_samples, float):
            min_samples = int(self.min_samples * n_samples)
        else:
            min_samples = self.min_samples

        min_samples = max(min_samples, n_features + 1)

        # Determine residual threshold
        if self.residual_threshold is None:
            # Use MAD of initial residuals
            X_design = np.column_stack([np.ones(n_samples), X])
            beta_init = np.linalg.lstsq(X_design, y, rcond=None)[0]
            residuals = y - X_design @ beta_init
            residual_threshold = 2.5 * 1.4826 * np.median(np.abs(residuals))
        else:
            residual_threshold = self.residual_threshold

        best_inliers = None
        best_n_inliers = 0
        best_beta = None

        for _ in range(self.max_trials):
            # Sample random subset
            idx = np.random.choice(n_samples, min_samples, replace=False)
            X_sub = X[idx]
            y_sub = y[idx]

            # Fit model
            try:
                X_design = np.column_stack([np.ones(len(idx)), X_sub])
                beta = np.linalg.lstsq(X_design, y_sub, rcond=None)[0]
            except np.linalg.LinAlgError:
                continue

            # Compute residuals on all data
            X_full = np.column_stack([np.ones(n_samples), X])
            residuals = np.abs(y - X_full @ beta)

            # Count inliers
            inliers = residuals < residual_threshold
            n_inliers = np.sum(inliers)

            if n_inliers > best_n_inliers:
                best_n_inliers = n_inliers
                best_inliers = inliers
                best_beta = beta

        # Refit on all inliers
        if best_inliers is not None and np.sum(best_inliers) > n_features:
            X_inliers = X[best_inliers]
            y_inliers = y[best_inliers]

            X_design = np.column_stack([np.ones(len(y_inliers)), X_inliers])
            best_beta = np.linalg.lstsq(X_design, y_inliers, rcond=None)[0]

        if best_beta is not None:
            self.intercept_ = best_beta[0]
            self.coef_ = best_beta[1:]
            self.inlier_mask_ = best_inliers
        else:
            # Fallback to OLS
            X_design = np.column_stack([np.ones(n_samples), X])
            beta = np.linalg.lstsq(X_design, y, rcond=None)[0]
            self.intercept_ = beta[0]
            self.coef_ = beta[1:]
            self.inlier_mask_ = np.ones(n_samples, dtype=bool)

        return self

    def infer(self, X: np.ndarray) -> np.ndarray:
        """Make predictions."""
        X = np.asarray(X)
        return X @ self.coef_ + self.intercept_
