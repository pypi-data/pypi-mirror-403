"""
Multicollinearity diagnostics.
"""

from __future__ import annotations

from typing import Tuple, Optional, Dict, Any, List
import numpy as np


def variance_inflation_factor(
    X: np.ndarray,
    exog_idx: Optional[int] = None,
) -> float | np.ndarray:
    """
    Variance Inflation Factor for detecting multicollinearity.

    VIF > 5 suggests problematic multicollinearity.
    VIF > 10 suggests severe multicollinearity.

    Parameters
    ----------
    X : ndarray of shape (n_samples, n_features)
        Design matrix (should NOT include constant).
    exog_idx : int, optional
        Index of variable to compute VIF for. If None, computes for all.

    Returns
    -------
    vif : float or ndarray
        VIF value(s).

    Examples
    --------
    >>> from nalyst.diagnostics import variance_inflation_factor
    >>> vif = variance_inflation_factor(X)
    >>> print(f"VIF values: {vif}")
    """
    X = np.asarray(X)

    if X.ndim == 1:
        return 1.0

    # Remove constant column if present
    if np.allclose(X[:, 0], 1):
        X = X[:, 1:]

    n, k = X.shape

    if exog_idx is not None:
        # VIF for single variable
        return _compute_vif(X, exog_idx)
    else:
        # VIF for all variables
        vif = np.zeros(k)
        for i in range(k):
            vif[i] = _compute_vif(X, i)
        return vif


def _compute_vif(X: np.ndarray, idx: int) -> float:
    """Compute VIF for a single variable."""
    n, k = X.shape

    # Target variable
    y = X[:, idx]

    # Other variables (with constant)
    mask = np.ones(k, dtype=bool)
    mask[idx] = False
    X_other = np.column_stack([np.ones(n), X[:, mask]])

    # Regress target on others
    beta = np.linalg.lstsq(X_other, y, rcond=None)[0]
    fitted = X_other @ beta

    # R-squared
    ss_res = np.sum((y - fitted) ** 2)
    ss_tot = np.sum((y - np.mean(y)) ** 2)

    if ss_tot == 0:
        return np.inf

    r_squared = 1 - ss_res / ss_tot

    if r_squared >= 1:
        return np.inf

    return 1 / (1 - r_squared)


def condition_number(X: np.ndarray) -> float:
    """
    Condition number of the design matrix.

    Measures overall multicollinearity.
    - < 30: Low multicollinearity
    - 30-100: Moderate
    - > 100: Severe

    Parameters
    ----------
    X : ndarray
        Design matrix.

    Returns
    -------
    cond : float
        Condition number.

    Examples
    --------
    >>> from nalyst.diagnostics import condition_number
    >>> cond = condition_number(X)
    >>> if cond > 30:
    ...     print("Multicollinearity may be a problem")
    """
    X = np.asarray(X)

    # Standardize columns (except constant)
    X_std = X.copy()
    if np.allclose(X[:, 0], 1):
        for i in range(1, X.shape[1]):
            std = np.std(X[:, i])
            if std > 0:
                X_std[:, i] = (X[:, i] - np.mean(X[:, i])) / std
    else:
        for i in range(X.shape[1]):
            std = np.std(X[:, i])
            if std > 0:
                X_std[:, i] = (X[:, i] - np.mean(X[:, i])) / std

    # Singular values
    s = np.linalg.svd(X_std, compute_uv=False)

    if s[-1] == 0:
        return np.inf

    return s[0] / s[-1]


def correlation_matrix(X: np.ndarray) -> np.ndarray:
    """
    Compute correlation matrix for design matrix.

    Parameters
    ----------
    X : ndarray of shape (n_samples, n_features)
        Design matrix.

    Returns
    -------
    corr : ndarray of shape (n_features, n_features)
        Correlation matrix.

    Examples
    --------
    >>> from nalyst.diagnostics import correlation_matrix
    >>> corr = correlation_matrix(X)
    """
    X = np.asarray(X)

    # Remove constant if present
    if np.allclose(X[:, 0], 1):
        X = X[:, 1:]

    return np.corrcoef(X, rowvar=False)


def eigenvalue_analysis(X: np.ndarray) -> Dict[str, np.ndarray]:
    """
    Eigenvalue analysis for multicollinearity.

    Parameters
    ----------
    X : ndarray
        Design matrix.

    Returns
    -------
    result : dict
        eigenvalues: Eigenvalues of X'X.
        condition_indices: Condition indices.
        variance_proportions: Variance decomposition.
    """
    X = np.asarray(X)

    # Standardize
    X_std = (X - X.mean(axis=0)) / (X.std(axis=0) + 1e-10)

    # X'X matrix
    XtX = X_std.T @ X_std

    # Eigenvalues
    eigenvalues = np.linalg.eigvalsh(XtX)
    eigenvalues = np.sort(eigenvalues)[::-1]

    # Condition indices
    condition_indices = np.sqrt(eigenvalues[0] / eigenvalues)

    # Variance decomposition proportions
    eigvecs = np.linalg.eigh(XtX)[1]
    phi = eigvecs ** 2

    variance_props = np.zeros_like(phi)
    for i in range(len(eigenvalues)):
        denom = np.sum(phi[:, :] / eigenvalues, axis=1)
        variance_props[:, i] = (phi[:, i] / eigenvalues[i]) / denom

    return {
        'eigenvalues': eigenvalues,
        'condition_indices': condition_indices,
        'variance_proportions': variance_props,
    }
