"""
Generalized Linear Models.
"""

from __future__ import annotations

from typing import Optional, Union, Dict, Any
import numpy as np
from scipy import linalg

from nalyst.core.foundation import BaseLearner
from nalyst.glm.families import Family, Gaussian, Binomial, Poisson
from nalyst.glm.links import Link


class GLM(BaseLearner):
    """
    Generalized Linear Model.

    Fits a GLM using Iteratively Reweighted Least Squares (IRLS).

    Parameters
    ----------
    family : Family or str
        Distribution family. Can be a Family instance or string:
        'gaussian', 'binomial', 'poisson', 'gamma', 'negative_binomial', 'tweedie'.
    link : Link, optional
        Link function. If None, uses family default.
    fit_intercept : bool, default=True
        Whether to fit an intercept.
    max_iter : int, default=100
        Maximum number of IRLS iterations.
    tol : float, default=1e-8
        Convergence tolerance.

    Attributes
    ----------
    coef_ : ndarray
        Coefficient estimates.
    intercept_ : float
        Intercept (if fit_intercept=True).
    n_iter_ : int
        Number of iterations.
    deviance_ : float
        Deviance of the fitted model.
    null_deviance_ : float
        Deviance of the null model.
    aic_ : float
        Akaike Information Criterion.
    bic_ : float
        Bayesian Information Criterion.

    Examples
    --------
    >>> from nalyst.glm import GLM, Poisson
    >>> model = GLM(family=Poisson())
    >>> model.train(X, y)
    >>> predictions = model.infer(X_new)
    """

    def __init__(
        self,
        family: Union[Family, str] = 'gaussian',
        link: Optional[Link] = None,
        fit_intercept: bool = True,
        max_iter: int = 100,
        tol: float = 1e-8,
    ):
        if isinstance(family, str):
            family = self._get_family(family)

        self.family = family
        self.fit_intercept = fit_intercept
        self.max_iter = max_iter
        self.tol = tol

        if link is not None:
            self.family.link = link

    def _get_family(self, name: str) -> Family:
        """Get family by name."""
        from nalyst.glm.families import (
            Gaussian, Binomial, Poisson, Gamma, NegativeBinomial, Tweedie
        )

        families = {
            'gaussian': Gaussian,
            'normal': Gaussian,
            'binomial': Binomial,
            'poisson': Poisson,
            'gamma': Gamma,
            'negative_binomial': NegativeBinomial,
            'negbinom': NegativeBinomial,
            'tweedie': Tweedie,
        }

        name_lower = name.lower()
        if name_lower not in families:
            raise ValueError(f"Unknown family: {name}")

        return families[name_lower]()

    def train(
        self,
        X: np.ndarray,
        y: np.ndarray,
        sample_weight: Optional[np.ndarray] = None,
        offset: Optional[np.ndarray] = None,
    ) -> "GLM":
        """
        Fit the GLM using IRLS.

        Parameters
        ----------
        X : ndarray of shape (n_samples, n_features)
            Feature matrix.
        y : ndarray of shape (n_samples,)
            Target values.
        sample_weight : ndarray, optional
            Sample weights.
        offset : ndarray, optional
            Offset term added to linear predictor.

        Returns
        -------
        self : GLM
        """
        X = np.asarray(X)
        y = np.asarray(y).flatten()

        n_samples, n_features = X.shape

        # Add intercept
        if self.fit_intercept:
            X = np.column_stack([np.ones(n_samples), X])
            n_features += 1

        # Initialize weights
        if sample_weight is None:
            sample_weight = np.ones(n_samples)
        else:
            sample_weight = np.asarray(sample_weight)

        # Initialize offset
        if offset is None:
            offset = np.zeros(n_samples)
        else:
            offset = np.asarray(offset)

        # Initialize mu
        mu = self._initialize_mu(y)
        eta = self.family.link(mu) - offset

        # IRLS
        converged = False

        for iteration in range(self.max_iter):
            # Working response and weights
            z = eta + (y - mu) * self.family.link.deriv(mu)
            w = sample_weight * self.family.weights(mu)

            # Weighted least squares
            sqrt_w = np.sqrt(np.maximum(w, 1e-10))
            X_tilde = X * sqrt_w[:, np.newaxis]
            z_tilde = z * sqrt_w

            # Solve normal equations
            try:
                coef, residues, rank, s = np.linalg.lstsq(X_tilde, z_tilde, rcond=None)
            except np.linalg.LinAlgError:
                coef = np.linalg.pinv(X_tilde) @ z_tilde

            # Update
            eta_new = X @ coef + offset
            mu_new = self.family.link.inverse(eta_new)

            # Check convergence
            if np.max(np.abs(eta_new - eta)) < self.tol:
                converged = True
                eta = eta_new
                mu = mu_new
                break

            eta = eta_new
            mu = mu_new

        self.n_iter_ = iteration + 1
        self.converged_ = converged

        # Store coefficients
        if self.fit_intercept:
            self.intercept_ = coef[0]
            self.coef_ = coef[1:]
        else:
            self.intercept_ = 0.0
            self.coef_ = coef

        # Store fitted values
        self._mu = mu
        self._X = X
        self._y = y
        self._n_samples = n_samples
        self._n_features = n_features

        # Compute statistics
        self._compute_statistics(X, y, mu, sample_weight)

        return self

    def _initialize_mu(self, y: np.ndarray) -> np.ndarray:
        """Initialize mean estimate."""
        # Use y with small adjustment
        if isinstance(self.family, Binomial):
            return np.clip(y, 0.01, 0.99)
        elif isinstance(self.family, (Poisson,)):
            return np.maximum(y, 0.1)
        else:
            return y.copy()

    def _compute_statistics(
        self,
        X: np.ndarray,
        y: np.ndarray,
        mu: np.ndarray,
        weights: np.ndarray,
    ):
        """Compute model statistics."""
        n = len(y)
        k = len(self.coef_) + (1 if self.fit_intercept else 0)

        # Deviance
        self.deviance_ = self.family.deviance(y, mu)

        # Null deviance (intercept-only model)
        mu_null = np.full_like(y, np.average(y, weights=weights))
        self.null_deviance_ = self.family.deviance(y, mu_null)

        # Scale parameter
        if isinstance(self.family, (Binomial, Poisson)):
            self.scale_ = 1.0
        else:
            self.scale_ = self.deviance_ / (n - k)

        # AIC and BIC
        log_lik = -0.5 * self.deviance_
        self.aic_ = -2 * log_lik + 2 * k
        self.bic_ = -2 * log_lik + k * np.log(n)

        # Pseudo R-squared
        self.pseudo_r2_ = 1 - self.deviance_ / self.null_deviance_

        # Standard errors
        self._compute_standard_errors(X, mu, weights)

    def _compute_standard_errors(
        self,
        X: np.ndarray,
        mu: np.ndarray,
        weights: np.ndarray,
    ):
        """Compute coefficient standard errors."""
        w = weights * self.family.weights(mu)

        # Fisher information matrix
        W = np.diag(w)
        XWX = X.T @ W @ X

        try:
            cov = np.linalg.inv(XWX) * self.scale_
            self.cov_params_ = cov

            if self.fit_intercept:
                self.bse_ = np.sqrt(np.diag(cov)[1:])
                self.intercept_se_ = np.sqrt(cov[0, 0])
            else:
                self.bse_ = np.sqrt(np.diag(cov))
                self.intercept_se_ = 0.0
        except np.linalg.LinAlgError:
            self.cov_params_ = None
            self.bse_ = np.full_like(self.coef_, np.nan)
            self.intercept_se_ = np.nan

    def infer(self, X: np.ndarray) -> np.ndarray:
        """
        Predict expected values.

        Parameters
        ----------
        X : ndarray of shape (n_samples, n_features)
            Feature matrix.

        Returns
        -------
        y_pred : ndarray of shape (n_samples,)
            Predicted expected values.
        """
        eta = self.predict_linear(X)
        return self.family.link.inverse(eta)

    def predict_linear(self, X: np.ndarray) -> np.ndarray:
        """
        Predict linear predictor (eta).

        Parameters
        ----------
        X : ndarray
            Feature matrix.

        Returns
        -------
        eta : ndarray
            Linear predictor values.
        """
        X = np.asarray(X)
        return X @ self.coef_ + self.intercept_

    def summary(self) -> Dict[str, Any]:
        """
        Get model summary.

        Returns
        -------
        summary : dict
            Model summary statistics.
        """
        from scipy import stats as sp_stats

        # z-statistics and p-values
        z_stats = self.coef_ / self.bse_
        p_values = 2 * sp_stats.norm.sf(np.abs(z_stats))

        return {
            'family': self.family.__class__.__name__,
            'link': self.family.link.__class__.__name__,
            'coefficients': self.coef_,
            'intercept': self.intercept_,
            'std_errors': self.bse_,
            'z_statistics': z_stats,
            'p_values': p_values,
            'deviance': self.deviance_,
            'null_deviance': self.null_deviance_,
            'aic': self.aic_,
            'bic': self.bic_,
            'pseudo_r2': self.pseudo_r2_,
            'n_iter': self.n_iter_,
            'converged': self.converged_,
        }

    def get_influence(self) -> Dict[str, np.ndarray]:
        """
        Get influence diagnostics.

        Returns
        -------
        diagnostics : dict
            Influence measures including leverage, Cook's distance, etc.
        """
        if not hasattr(self, '_X'):
            raise ValueError("Model must be trained first")

        X = self._X
        y = self._y
        mu = self._mu

        # Hat matrix diagonal (leverage)
        w = self.family.weights(mu)
        W = np.diag(np.sqrt(w))
        X_tilde = W @ X

        try:
            H = X_tilde @ np.linalg.inv(X_tilde.T @ X_tilde) @ X_tilde.T
            leverage = np.diag(H)
        except np.linalg.LinAlgError:
            leverage = np.zeros(len(y))

        # Residuals
        deviance_resid = self.family.deviance_residuals(y, mu)
        pearson_resid = (y - mu) / np.sqrt(self.family.variance(mu))

        # Standardized residuals
        std_resid = pearson_resid / np.sqrt(self.scale_ * (1 - leverage))

        # Cook's distance
        k = len(self.coef_) + (1 if self.fit_intercept else 0)
        cooks_d = (std_resid ** 2 * leverage) / (k * (1 - leverage))

        return {
            'leverage': leverage,
            'deviance_residuals': deviance_resid,
            'pearson_residuals': pearson_resid,
            'standardized_residuals': std_resid,
            'cooks_distance': cooks_d,
        }
