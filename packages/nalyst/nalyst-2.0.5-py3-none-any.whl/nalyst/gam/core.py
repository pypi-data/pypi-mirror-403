"""
GAM model implementations.
"""

from __future__ import annotations

from typing import Optional, List, Union, Callable
import numpy as np
from scipy import linalg


class GAM:
    """
    Generalized Additive Model.

    Models the response as a sum of smooth functions of predictors.

    Parameters
    ----------
    terms : list of Term objects
        Model terms (splines, linear, factors).
    distribution : str, default='gaussian'
        Response distribution ('gaussian', 'binomial', 'poisson', 'gamma').
    link : str, default='identity'
        Link function ('identity', 'log', 'logit', 'inverse').
    max_iter : int, default=100
        Maximum IRLS iterations.
    tol : float, default=1e-6
        Convergence tolerance.

    Attributes
    ----------
    coef_ : ndarray
        Spline coefficients.
    edf_ : float
        Effective degrees of freedom.
    gcv_ : float
        GCV score.

    Examples
    --------
    >>> from nalyst.gam import GAM, s, l
    >>> gam = GAM(terms=[s(0, n_splines=10), s(1, n_splines=10), l(2)])
    >>> gam.train(X, y)
    >>> y_pred = gam.infer(X_new)
    """

    def __init__(
        self,
        terms: Optional[List] = None,
        distribution: str = 'gaussian',
        link: str = 'identity',
        max_iter: int = 100,
        tol: float = 1e-6,
    ):
        self.terms = terms if terms is not None else []
        self.distribution = distribution
        self.link = link
        self.max_iter = max_iter
        self.tol = tol

    def _get_link_function(self) -> tuple:
        """Get link and inverse link functions."""
        if self.link == 'identity':
            return lambda x: x, lambda x: x
        elif self.link == 'log':
            return np.log, np.exp
        elif self.link == 'logit':
            return (
                lambda x: np.log(x / (1 - x + 1e-10)),
                lambda x: 1 / (1 + np.exp(-x))
            )
        elif self.link == 'inverse':
            return lambda x: 1 / (x + 1e-10), lambda x: 1 / (x + 1e-10)
        else:
            raise ValueError(f"Unknown link: {self.link}")

    def _get_weights(self, mu: np.ndarray) -> np.ndarray:
        """Get IRLS weights based on distribution."""
        eps = 1e-10

        if self.distribution == 'gaussian':
            return np.ones_like(mu)
        elif self.distribution == 'binomial':
            return mu * (1 - mu) + eps
        elif self.distribution == 'poisson':
            return mu + eps
        elif self.distribution == 'gamma':
            return mu ** 2 + eps
        else:
            return np.ones_like(mu)

    def train(self, X: np.ndarray, y: np.ndarray) -> "GAM":
        """
        Fit the GAM.

        Parameters
        ----------
        X : ndarray of shape (n_samples, n_features)
            Feature matrix.
        y : ndarray of shape (n_samples,)
            Target values.

        Returns
        -------
        self
        """
        X = np.asarray(X)
        y = np.asarray(y).flatten()

        n_samples = len(y)

        # If no terms specified, create spline for each feature
        if not self.terms:
            from nalyst.gam.terms import SplineTerm
            self.terms = [SplineTerm(i) for i in range(X.shape[1])]

        # Build design matrix
        self.basis_matrices_ = []
        self.penalty_matrices_ = []

        design_parts = [np.ones((n_samples, 1))]  # Intercept

        for term in self.terms:
            B, P = term.build(X)
            self.basis_matrices_.append(B)
            self.penalty_matrices_.append(P)
            design_parts.append(B)

        # Full design matrix
        self.design_ = np.hstack(design_parts)
        n_coef = self.design_.shape[1]

        # Build penalty matrix
        penalty_sizes = [1] + [B.shape[1] for B in self.basis_matrices_]
        self.penalty_ = np.zeros((n_coef, n_coef))

        idx = 1  # Skip intercept
        for i, P in enumerate(self.penalty_matrices_):
            size = penalty_sizes[i + 1]
            self.penalty_[idx:idx + size, idx:idx + size] = P
            idx += size

        # Link functions
        link_fn, inv_link = self._get_link_function()

        # Initialize
        if self.distribution == 'binomial':
            mu = np.clip(y, 0.01, 0.99)
        elif self.distribution == 'poisson':
            mu = np.maximum(y, 0.1)
        else:
            mu = y.copy()

        eta = link_fn(mu)

        # Smoothing parameter selection via GCV
        self.lambda_ = self._select_smoothing(X, y)

        # IRLS
        coef = np.zeros(n_coef)

        for iteration in range(self.max_iter):
            # Working weights
            W = self._get_weights(mu)

            # Working response
            z = eta + (y - mu) / (W + 1e-10)

            # Weighted least squares with penalty
            WD = self.design_ * np.sqrt(W)[:, None]
            wz = z * np.sqrt(W)

            # Solve penalized least squares
            A = WD.T @ WD + self.lambda_ * self.penalty_
            b = WD.T @ wz

            try:
                coef_new = linalg.solve(A, b, assume_a='pos')
            except linalg.LinAlgError:
                coef_new = np.linalg.lstsq(A, b, rcond=None)[0]

            # Update
            eta = self.design_ @ coef_new
            mu = inv_link(eta)

            # Clip for numerical stability
            if self.distribution == 'binomial':
                mu = np.clip(mu, 1e-10, 1 - 1e-10)
            elif self.distribution in ['poisson', 'gamma']:
                mu = np.maximum(mu, 1e-10)

            # Check convergence
            if np.max(np.abs(coef_new - coef)) < self.tol:
                coef = coef_new
                break

            coef = coef_new

        self.coef_ = coef
        self.intercept_ = coef[0]

        # Calculate effective degrees of freedom
        W = self._get_weights(mu)
        WD = self.design_ * np.sqrt(W)[:, None]
        A = WD.T @ WD + self.lambda_ * self.penalty_

        try:
            A_inv = linalg.inv(A)
            H = WD @ A_inv @ WD.T
            self.edf_ = np.trace(H)
        except linalg.LinAlgError:
            self.edf_ = n_coef

        # GCV score
        residuals = y - mu
        self.gcv_ = np.sum(residuals ** 2) / (n_samples - self.edf_) ** 2

        return self

    def _select_smoothing(self, X: np.ndarray, y: np.ndarray) -> float:
        """Select smoothing parameter via GCV."""
        # Grid search over lambda values
        lambdas = np.logspace(-3, 5, 20)
        best_gcv = np.inf
        best_lambda = 1.0

        n_samples = len(y)

        for lam in lambdas:
            # Fit with this lambda
            A = self.design_.T @ self.design_ + lam * self.penalty_
            try:
                coef = linalg.solve(A, self.design_.T @ y, assume_a='pos')
            except:
                continue

            # Predictions
            y_pred = self.design_ @ coef

            # Hat matrix trace (approximation)
            try:
                A_inv = linalg.inv(A)
                edf = np.trace(self.design_ @ A_inv @ self.design_.T)
            except:
                edf = self.design_.shape[1]

            # GCV
            rss = np.sum((y - y_pred) ** 2)
            gcv = n_samples * rss / (n_samples - edf) ** 2

            if gcv < best_gcv:
                best_gcv = gcv
                best_lambda = lam

        return best_lambda

    def infer(self, X: np.ndarray) -> np.ndarray:
        """
        Predict using the fitted GAM.

        Parameters
        ----------
        X : ndarray of shape (n_samples, n_features)
            Features.

        Returns
        -------
        y_pred : ndarray
            Predictions on response scale.
        """
        X = np.asarray(X)
        n_samples = len(X)

        # Build design for new data
        design_parts = [np.ones((n_samples, 1))]

        for term in self.terms:
            B, _ = term.build(X)
            design_parts.append(B)

        design = np.hstack(design_parts)

        # Linear predictor
        eta = design @ self.coef_

        # Apply inverse link
        _, inv_link = self._get_link_function()

        return inv_link(eta)

    def predict(self, X: np.ndarray) -> np.ndarray:
        """Alias for infer."""
        return self.infer(X)

    def partial_dependence(
        self,
        X: np.ndarray,
        feature: int,
        n_points: int = 100,
    ) -> tuple:
        """
        Calculate partial dependence for a feature.

        Parameters
        ----------
        X : ndarray
            Feature matrix.
        feature : int
            Feature index.
        n_points : int
            Number of grid points.

        Returns
        -------
        grid : ndarray
            Grid values.
        effects : ndarray
            Partial effects.
        """
        X = np.asarray(X)

        # Find the term for this feature
        term_idx = None
        for i, term in enumerate(self.terms):
            if hasattr(term, 'feature') and term.feature == feature:
                term_idx = i
                break

        if term_idx is None:
            raise ValueError(f"No term found for feature {feature}")

        # Grid over feature range
        feature_min = X[:, feature].min()
        feature_max = X[:, feature].max()
        grid = np.linspace(feature_min, feature_max, n_points)

        # Get coefficients for this term
        coef_start = 1  # Skip intercept
        for i in range(term_idx):
            coef_start += self.basis_matrices_[i].shape[1]

        coef_end = coef_start + self.basis_matrices_[term_idx].shape[1]
        term_coef = self.coef_[coef_start:coef_end]

        # Evaluate term on grid
        X_grid = np.zeros((n_points, X.shape[1]))
        X_grid[:, feature] = grid

        B, _ = self.terms[term_idx].build(X_grid)
        effects = B @ term_coef

        return grid, effects


class LinearGAM(GAM):
    """
    GAM with Gaussian distribution and identity link.

    For continuous response regression.
    """

    def __init__(
        self,
        terms: Optional[List] = None,
        max_iter: int = 100,
        tol: float = 1e-6,
    ):
        super().__init__(
            terms=terms,
            distribution='gaussian',
            link='identity',
            max_iter=max_iter,
            tol=tol,
        )


class LogisticGAM(GAM):
    """
    GAM with binomial distribution and logit link.

    For binary classification.
    """

    def __init__(
        self,
        terms: Optional[List] = None,
        max_iter: int = 100,
        tol: float = 1e-6,
    ):
        super().__init__(
            terms=terms,
            distribution='binomial',
            link='logit',
            max_iter=max_iter,
            tol=tol,
        )

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """
        Predict class probabilities.

        Returns
        -------
        proba : ndarray of shape (n_samples, 2)
            Class probabilities.
        """
        p1 = self.infer(X)
        return np.column_stack([1 - p1, p1])


class PoissonGAM(GAM):
    """
    GAM with Poisson distribution and log link.

    For count data.
    """

    def __init__(
        self,
        terms: Optional[List] = None,
        max_iter: int = 100,
        tol: float = 1e-6,
    ):
        super().__init__(
            terms=terms,
            distribution='poisson',
            link='log',
            max_iter=max_iter,
            tol=tol,
        )


class GammaGAM(GAM):
    """
    GAM with Gamma distribution and log link.

    For positive continuous data.
    """

    def __init__(
        self,
        terms: Optional[List] = None,
        max_iter: int = 100,
        tol: float = 1e-6,
    ):
        super().__init__(
            terms=terms,
            distribution='gamma',
            link='log',
            max_iter=max_iter,
            tol=tol,
        )
