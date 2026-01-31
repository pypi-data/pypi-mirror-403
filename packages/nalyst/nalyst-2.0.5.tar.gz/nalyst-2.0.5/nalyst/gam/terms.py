"""
GAM term definitions for building model formulae.
"""

from __future__ import annotations

from typing import Optional
import numpy as np


class BaseTerm:
    """Base class for GAM terms."""

    def build(self, X: np.ndarray) -> tuple:
        """
        Build basis and penalty matrices.

        Returns
        -------
        basis : ndarray
            Basis matrix.
        penalty : ndarray
            Penalty matrix.
        """
        raise NotImplementedError


class SplineTerm(BaseTerm):
    """
    Smooth spline term.

    Parameters
    ----------
    feature : int
        Feature index.
    n_splines : int, default=10
        Number of basis functions.
    spline_order : int, default=3
        B-spline order (3 = cubic).
    lam : float, default=0.6
        Smoothing penalty.

    Examples
    --------
    >>> term = SplineTerm(0, n_splines=15)
    >>> B, P = term.build(X)
    """

    def __init__(
        self,
        feature: int,
        n_splines: int = 10,
        spline_order: int = 3,
        lam: float = 0.6,
    ):
        self.feature = feature
        self.n_splines = n_splines
        self.spline_order = spline_order
        self.lam = lam
        self._knots = None

    def build(self, X: np.ndarray) -> tuple:
        """Build B-spline basis and penalty matrices."""
        x = X[:, self.feature]
        n = len(x)
        k = self.n_splines

        # Set up knots
        if self._knots is None:
            x_min, x_max = x.min(), x.max()
            padding = (x_max - x_min) * 0.01

            # Interior knots
            n_interior = k - self.spline_order - 1
            interior = np.linspace(x_min, x_max, n_interior + 2)[1:-1]

            # Full knot sequence with boundary knots
            self._knots = np.concatenate([
                np.repeat(x_min - padding, self.spline_order + 1),
                interior,
                np.repeat(x_max + padding, self.spline_order + 1),
            ])

        # Build B-spline basis
        basis = self._bspline_basis(x)

        # Second derivative penalty (thin-plate spline style)
        penalty = self._build_penalty(k)

        return basis, penalty * self.lam

    def _bspline_basis(self, x: np.ndarray) -> np.ndarray:
        """Evaluate B-spline basis at x."""
        n = len(x)
        k = self.n_splines
        d = self.spline_order
        t = self._knots

        # Use recursive B-spline formula
        basis = np.zeros((n, k))

        for i in range(k):
            basis[:, i] = self._bspline(x, i, d, t)

        return basis

    def _bspline(
        self,
        x: np.ndarray,
        i: int,
        d: int,
        t: np.ndarray,
    ) -> np.ndarray:
        """Recursive B-spline basis function."""
        if d == 0:
            return ((x >= t[i]) & (x < t[i + 1])).astype(float)

        # Avoid division by zero
        denom1 = t[i + d] - t[i]
        denom2 = t[i + d + 1] - t[i + 1]

        term1 = np.zeros_like(x)
        term2 = np.zeros_like(x)

        if denom1 > 0:
            term1 = (x - t[i]) / denom1 * self._bspline(x, i, d - 1, t)

        if denom2 > 0:
            term2 = (t[i + d + 1] - x) / denom2 * self._bspline(x, i + 1, d - 1, t)

        return term1 + term2

    def _build_penalty(self, k: int) -> np.ndarray:
        """Build second-difference penalty matrix."""
        # Second-difference matrix
        D = np.zeros((k - 2, k))
        for i in range(k - 2):
            D[i, i] = 1
            D[i, i + 1] = -2
            D[i, i + 2] = 1

        return D.T @ D


class LinearTerm(BaseTerm):
    """
    Linear (unsmoothed) term.

    Parameters
    ----------
    feature : int
        Feature index.

    Examples
    --------
    >>> term = LinearTerm(2)  # Linear effect for feature 2
    """

    def __init__(self, feature: int):
        self.feature = feature

    def build(self, X: np.ndarray) -> tuple:
        """Build linear term (no penalty)."""
        x = X[:, self.feature].reshape(-1, 1)

        # Standardize
        basis = (x - x.mean()) / (x.std() + 1e-10)

        # No penalty for linear terms
        penalty = np.zeros((1, 1))

        return basis, penalty


class FactorTerm(BaseTerm):
    """
    Categorical factor term.

    Parameters
    ----------
    feature : int
        Feature index.
    levels : list, optional
        Factor levels. If None, inferred from data.

    Examples
    --------
    >>> term = FactorTerm(0)  # Categorical effect
    """

    def __init__(self, feature: int, levels: Optional[list] = None):
        self.feature = feature
        self.levels = levels
        self._fitted_levels = None

    def build(self, X: np.ndarray) -> tuple:
        """Build dummy encoding."""
        x = X[:, self.feature]

        if self._fitted_levels is None:
            self._fitted_levels = (
                self.levels if self.levels is not None
                else np.unique(x).tolist()
            )

        levels = self._fitted_levels
        k = len(levels)
        n = len(x)

        # Dummy encoding (reference level is first)
        basis = np.zeros((n, k - 1))

        for i, level in enumerate(levels[1:]):
            basis[:, i] = (x == level).astype(float)

        # No penalty
        penalty = np.zeros((k - 1, k - 1))

        return basis, penalty


class TensorTerm(BaseTerm):
    """
    Tensor product smooth for interactions.

    Parameters
    ----------
    feature1 : int
        First feature index.
    feature2 : int
        Second feature index.
    n_splines : int, default=5
        Number of basis functions per dimension.
    lam : float, default=0.6
        Smoothing penalty.

    Examples
    --------
    >>> term = TensorTerm(0, 1)  # Smooth interaction between features 0 and 1
    """

    def __init__(
        self,
        feature1: int,
        feature2: int,
        n_splines: int = 5,
        lam: float = 0.6,
    ):
        self.feature1 = feature1
        self.feature2 = feature2
        self.n_splines = n_splines
        self.lam = lam
        self._term1 = SplineTerm(feature1, n_splines, lam=0)
        self._term2 = SplineTerm(feature2, n_splines, lam=0)

    def build(self, X: np.ndarray) -> tuple:
        """Build tensor product basis."""
        # Get marginal bases
        B1, P1 = self._term1.build(X)
        B2, P2 = self._term2.build(X)

        n = len(X)
        k1 = B1.shape[1]
        k2 = B2.shape[1]

        # Tensor product: row-wise Kronecker product
        basis = np.zeros((n, k1 * k2))

        for i in range(n):
            basis[i, :] = np.outer(B1[i, :], B2[i, :]).flatten()

        # Tensor penalty
        I1 = np.eye(k1)
        I2 = np.eye(k2)

        # Penalty: P1 x I2 + I1 x P2
        P1_expanded = np.kron(P1, I2)
        P2_expanded = np.kron(I1, P2)

        penalty = self.lam * (P1_expanded + P2_expanded)

        return basis, penalty


# Convenience functions for creating terms
def s(
    feature: int,
    n_splines: int = 10,
    spline_order: int = 3,
    lam: float = 0.6,
) -> SplineTerm:
    """
    Create a smooth spline term.

    Parameters
    ----------
    feature : int
        Feature index.
    n_splines : int, default=10
        Number of basis functions.
    spline_order : int, default=3
        Spline order (3 = cubic).
    lam : float, default=0.6
        Smoothing parameter.

    Returns
    -------
    SplineTerm

    Examples
    --------
    >>> from nalyst.gam import LinearGAM, s
    >>> gam = LinearGAM(terms=[s(0), s(1)])
    >>> gam.train(X, y)
    """
    return SplineTerm(feature, n_splines, spline_order, lam)


def l(feature: int) -> LinearTerm:
    """
    Create a linear term.

    Parameters
    ----------
    feature : int
        Feature index.

    Returns
    -------
    LinearTerm

    Examples
    --------
    >>> from nalyst.gam import LinearGAM, l
    >>> gam = LinearGAM(terms=[l(0)])  # Simple linear regression
    """
    return LinearTerm(feature)


def f(feature: int, levels: Optional[list] = None) -> FactorTerm:
    """
    Create a factor (categorical) term.

    Parameters
    ----------
    feature : int
        Feature index.
    levels : list, optional
        Factor levels.

    Returns
    -------
    FactorTerm

    Examples
    --------
    >>> from nalyst.gam import LinearGAM, f
    >>> gam = LinearGAM(terms=[f(0, levels=['A', 'B', 'C'])])
    """
    return FactorTerm(feature, levels)


def te(
    feature1: int,
    feature2: int,
    n_splines: int = 5,
    lam: float = 0.6,
) -> TensorTerm:
    """
    Create a tensor product smooth term.

    Parameters
    ----------
    feature1 : int
        First feature index.
    feature2 : int
        Second feature index.
    n_splines : int, default=5
        Basis functions per dimension.
    lam : float, default=0.6
        Smoothing parameter.

    Returns
    -------
    TensorTerm

    Examples
    --------
    >>> from nalyst.gam import LinearGAM, te
    >>> gam = LinearGAM(terms=[te(0, 1)])  # Smooth interaction
    """
    return TensorTerm(feature1, feature2, n_splines, lam)
