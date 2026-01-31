"""
Model specification tests.
"""

from __future__ import annotations

from typing import Tuple, Optional, Dict, Any
import numpy as np
from scipy import stats


def reset_test(
    y: np.ndarray,
    X: np.ndarray,
    power: int = 3,
) -> Tuple[float, float]:
    """
    RESET specification test (Ramsey's RESET).

    Tests for omitted nonlinearities by including powers of fitted values.

    Parameters
    ----------
    y : ndarray
        Dependent variable.
    X : ndarray
        Design matrix.
    power : int, default=3
        Maximum power of fitted values to include (2 = squared, 3 = squared + cubed).

    Returns
    -------
    fvalue : float
        F-statistic.
    pvalue : float
        P-value.

    Examples
    --------
    >>> from nalyst.diagnostics import reset_test
    >>> f, p = reset_test(y, X)
    >>> if p < 0.05:
    ...     print("Model may be misspecified")
    """
    y = np.asarray(y).flatten()
    X = np.asarray(X)

    n = len(y)

    if X.ndim == 1:
        X = X.reshape(-1, 1)

    if not np.allclose(X[:, 0], 1):
        X = np.column_stack([np.ones(n), X])

    k = X.shape[1]

    # Fit original model
    beta = np.linalg.lstsq(X, y, rcond=None)[0]
    fitted = X @ beta
    resid = y - fitted

    ssr_restricted = np.sum(resid ** 2)

    # Add powers of fitted values
    X_aug = X.copy()
    for p in range(2, power + 1):
        X_aug = np.column_stack([X_aug, fitted ** p])

    k_aug = X_aug.shape[1]

    # Fit augmented model
    beta_aug = np.linalg.lstsq(X_aug, y, rcond=None)[0]
    fitted_aug = X_aug @ beta_aug
    resid_aug = y - fitted_aug

    ssr_unrestricted = np.sum(resid_aug ** 2)

    # F-test
    df1 = k_aug - k
    df2 = n - k_aug

    fvalue = ((ssr_restricted - ssr_unrestricted) / df1) / (ssr_unrestricted / df2)
    pvalue = stats.f.sf(fvalue, df1, df2)

    return fvalue, pvalue


def harvey_collier(
    y: np.ndarray,
    X: np.ndarray,
) -> Tuple[float, float]:
    """
    Harvey-Collier test for linearity.

    Uses recursive residuals to test for linearity.

    Parameters
    ----------
    y : ndarray
        Dependent variable.
    X : ndarray
        Design matrix.

    Returns
    -------
    tvalue : float
        T-statistic.
    pvalue : float
        P-value.

    Examples
    --------
    >>> from nalyst.diagnostics import harvey_collier
    >>> t, p = harvey_collier(y, X)
    """
    y = np.asarray(y).flatten()
    X = np.asarray(X)

    n = len(y)

    if X.ndim == 1:
        X = X.reshape(-1, 1)

    if not np.allclose(X[:, 0], 1):
        X = np.column_stack([np.ones(n), X])

    k = X.shape[1]

    # Compute recursive residuals
    rec_resid = recursive_residuals(y, X)

    # Remove NaN values
    rec_resid = rec_resid[~np.isnan(rec_resid)]
    m = len(rec_resid)

    if m < 3:
        return np.nan, np.nan

    # T-test on mean of recursive residuals
    mean_resid = np.mean(rec_resid)
    std_resid = np.std(rec_resid, ddof=1)
    se = std_resid / np.sqrt(m)

    tvalue = mean_resid / se
    pvalue = 2 * stats.t.sf(abs(tvalue), m - 1)

    return tvalue, pvalue


def recursive_residuals(
    y: np.ndarray,
    X: np.ndarray,
) -> np.ndarray:
    """
    Compute recursive residuals (CUSUM residuals).

    Parameters
    ----------
    y : ndarray
        Dependent variable.
    X : ndarray
        Design matrix.

    Returns
    -------
    rec_resid : ndarray
        Recursive residuals. First k values are NaN.

    Examples
    --------
    >>> from nalyst.diagnostics import recursive_residuals
    >>> rec_resid = recursive_residuals(y, X)
    """
    y = np.asarray(y).flatten()
    X = np.asarray(X)

    n = len(y)

    if X.ndim == 1:
        X = X.reshape(-1, 1)

    if not np.allclose(X[:, 0], 1):
        X = np.column_stack([np.ones(n), X])

    k = X.shape[1]

    rec_resid = np.full(n, np.nan)

    # Initialize with first k observations
    XtX = np.zeros((k, k))
    Xty = np.zeros(k)

    for t in range(k):
        XtX += np.outer(X[t], X[t])
        Xty += X[t] * y[t]

    # Recursive estimation
    for t in range(k, n):
        # Current observation
        x_t = X[t]
        y_t = y[t]

        # Inverse update (Sherman-Morrison)
        try:
            XtX_inv = np.linalg.inv(XtX)
        except np.linalg.LinAlgError:
            XtX_inv = np.linalg.pinv(XtX)

        # One-step-ahead forecast
        beta_t = XtX_inv @ Xty
        y_pred = x_t @ beta_t

        # Forecast error
        v_t = y_t - y_pred

        # Variance of forecast error
        f_t = 1 + x_t @ XtX_inv @ x_t

        # Recursive residual
        rec_resid[t] = v_t / np.sqrt(f_t)

        # Update
        XtX += np.outer(x_t, x_t)
        Xty += x_t * y_t

    return rec_resid


def cusum_test(
    y: np.ndarray,
    X: np.ndarray,
) -> Dict[str, Any]:
    """
    CUSUM test for parameter stability.

    Parameters
    ----------
    y : ndarray
        Dependent variable.
    X : ndarray
        Design matrix.

    Returns
    -------
    result : dict
        cusum: CUSUM values.
        bounds: Critical bounds at 5% level.
        statistic: Maximum deviation statistic.
        pvalue: Approximate p-value.

    Examples
    --------
    >>> from nalyst.diagnostics import cusum_test
    >>> result = cusum_test(y, X)
    """
    y = np.asarray(y).flatten()
    X = np.asarray(X)

    n = len(y)

    if X.ndim == 1:
        X = X.reshape(-1, 1)

    k = X.shape[1]

    # Recursive residuals
    rec_resid = recursive_residuals(y, X)
    rec_resid = rec_resid[k:]  # Remove NaN values
    m = len(rec_resid)

    if m < 3:
        return {'cusum': None, 'pvalue': np.nan}

    # Estimate sigma from recursive residuals
    sigma = np.std(rec_resid, ddof=1)

    # CUSUM
    cusum = np.cumsum(rec_resid) / sigma

    # Bounds (5% significance)
    # Uses Brownian motion critical values
    t_vals = np.arange(1, m + 1) / m
    bounds_upper = 0.948 * np.sqrt(m) + 2 * 0.948 * np.sqrt(m) * t_vals
    bounds_lower = -bounds_upper

    # Test statistic
    max_deviation = np.max(np.abs(cusum) / np.sqrt(np.arange(1, m + 1)))

    # Approximate p-value
    pvalue = 2 * (1 - stats.norm.cdf(max_deviation))

    return {
        'cusum': cusum,
        'bounds_upper': bounds_upper,
        'bounds_lower': bounds_lower,
        'statistic': max_deviation,
        'pvalue': pvalue,
    }
