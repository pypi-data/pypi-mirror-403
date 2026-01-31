"""
Heteroscedasticity tests.
"""

from __future__ import annotations

from typing import Tuple, Optional, Dict, Any
import numpy as np
from scipy import stats


def het_breuschpagan(
    resid: np.ndarray,
    exog: np.ndarray,
) -> Tuple[float, float, float, float]:
    """
    Breusch-Pagan Lagrange Multiplier test for heteroscedasticity.

    Tests whether variance of residuals depends on exogenous variables.

    Parameters
    ----------
    resid : ndarray
        Residuals from regression.
    exog : ndarray
        Exogenous variables (design matrix).

    Returns
    -------
    lm : float
        Lagrange Multiplier test statistic.
    lm_pvalue : float
        P-value for LM test.
    fvalue : float
        F-statistic.
    f_pvalue : float
        P-value for F-test.

    Examples
    --------
    >>> from nalyst.diagnostics import het_breuschpagan
    >>> lm, lm_p, f, f_p = het_breuschpagan(residuals, X)
    >>> if lm_p < 0.05:
    ...     print("Heteroscedasticity detected")
    """
    resid = np.asarray(resid).flatten()
    exog = np.asarray(exog)

    n = len(resid)

    if exog.ndim == 1:
        exog = exog.reshape(-1, 1)

    # Add constant if not present
    if not np.allclose(exog[:, 0], 1):
        exog = np.column_stack([np.ones(n), exog])

    k = exog.shape[1]

    # Squared residuals
    resid_sq = resid ** 2

    # Regress squared residuals on exogenous variables
    beta = np.linalg.lstsq(exog, resid_sq, rcond=None)[0]
    fitted = exog @ beta

    # SSR and SST
    ssr = np.sum((fitted - np.mean(resid_sq)) ** 2)
    sst = np.sum((resid_sq - np.mean(resid_sq)) ** 2)

    # LM statistic
    r_squared = ssr / sst
    lm = n * r_squared
    lm_pvalue = stats.chi2.sf(lm, k - 1)

    # F statistic
    sse = np.sum((resid_sq - fitted) ** 2)
    fvalue = (ssr / (k - 1)) / (sse / (n - k))
    f_pvalue = stats.f.sf(fvalue, k - 1, n - k)

    return lm, lm_pvalue, fvalue, f_pvalue


def het_white(
    resid: np.ndarray,
    exog: np.ndarray,
) -> Tuple[float, float, float, float]:
    """
    White's Lagrange Multiplier test for heteroscedasticity.

    More general than Breusch-Pagan, includes squares and cross-products.

    Parameters
    ----------
    resid : ndarray
        Residuals from regression.
    exog : ndarray
        Exogenous variables.

    Returns
    -------
    lm : float
        LM test statistic.
    lm_pvalue : float
        P-value for LM test.
    fvalue : float
        F-statistic.
    f_pvalue : float
        P-value for F-test.

    Examples
    --------
    >>> from nalyst.diagnostics import het_white
    >>> lm, lm_p, f, f_p = het_white(residuals, X)
    """
    resid = np.asarray(resid).flatten()
    exog = np.asarray(exog)

    n = len(resid)

    if exog.ndim == 1:
        exog = exog.reshape(-1, 1)

    # Remove constant if present
    if np.allclose(exog[:, 0], 1):
        exog = exog[:, 1:]

    k = exog.shape[1]

    # Create White's auxiliary regression variables
    # Include squares and cross-products
    aux_vars = [np.ones(n)]

    for i in range(k):
        aux_vars.append(exog[:, i])
        aux_vars.append(exog[:, i] ** 2)

    for i in range(k):
        for j in range(i + 1, k):
            aux_vars.append(exog[:, i] * exog[:, j])

    X_aux = np.column_stack(aux_vars)

    # Squared residuals
    resid_sq = resid ** 2

    # Regress
    beta = np.linalg.lstsq(X_aux, resid_sq, rcond=None)[0]
    fitted = X_aux @ beta

    # LM statistic
    ssr = np.sum((fitted - np.mean(resid_sq)) ** 2)
    sst = np.sum((resid_sq - np.mean(resid_sq)) ** 2)

    r_squared = ssr / sst
    df = X_aux.shape[1] - 1

    lm = n * r_squared
    lm_pvalue = stats.chi2.sf(lm, df)

    # F statistic
    sse = np.sum((resid_sq - fitted) ** 2)
    fvalue = (ssr / df) / (sse / (n - X_aux.shape[1]))
    f_pvalue = stats.f.sf(fvalue, df, n - X_aux.shape[1])

    return lm, lm_pvalue, fvalue, f_pvalue


def het_goldfeldquandt(
    y: np.ndarray,
    X: np.ndarray,
    split: Optional[float] = None,
    drop: float = 0.2,
    alternative: str = 'two-sided',
) -> Tuple[float, float, str]:
    """
    Goldfeld-Quandt test for heteroscedasticity.

    Tests if variance differs between two subsets of the data.

    Parameters
    ----------
    y : ndarray
        Dependent variable.
    X : ndarray
        Exogenous variables.
    split : float, optional
        Split point (fraction of data). Default is 0.5.
    drop : float, default=0.2
        Fraction of observations to drop in the middle.
    alternative : str, default='two-sided'
        Alternative hypothesis: 'two-sided', 'increasing', 'decreasing'.

    Returns
    -------
    fvalue : float
        F-statistic.
    pvalue : float
        P-value.
    ordering : str
        Which group has larger variance.

    Examples
    --------
    >>> from nalyst.diagnostics import het_goldfeldquandt
    >>> f, p, order = het_goldfeldquandt(y, X)
    """
    y = np.asarray(y).flatten()
    X = np.asarray(X)

    n = len(y)

    if X.ndim == 1:
        X = X.reshape(-1, 1)

    # Sort by first regressor
    sort_idx = np.argsort(X[:, 0] if not np.allclose(X[:, 0], 1) else X[:, 1])
    y_sorted = y[sort_idx]
    X_sorted = X[sort_idx]

    # Split data
    if split is None:
        split = 0.5

    drop_n = int(n * drop)
    n_first = int((n - drop_n) * split)
    n_second = n - drop_n - n_first

    # First subset
    y1 = y_sorted[:n_first]
    X1 = X_sorted[:n_first]

    # Second subset
    y2 = y_sorted[-n_second:]
    X2 = X_sorted[-n_second:]

    # Fit regressions
    beta1 = np.linalg.lstsq(X1, y1, rcond=None)[0]
    resid1 = y1 - X1 @ beta1
    sse1 = np.sum(resid1 ** 2)

    beta2 = np.linalg.lstsq(X2, y2, rcond=None)[0]
    resid2 = y2 - X2 @ beta2
    sse2 = np.sum(resid2 ** 2)

    # Degrees of freedom
    k = X.shape[1]
    df1 = n_first - k
    df2 = n_second - k

    # F statistic
    fvalue = (sse2 / df2) / (sse1 / df1)

    # P-value
    if alternative == 'increasing':
        pvalue = stats.f.sf(fvalue, df2, df1)
        ordering = 'increasing' if fvalue > 1 else 'decreasing'
    elif alternative == 'decreasing':
        pvalue = stats.f.cdf(fvalue, df2, df1)
        ordering = 'decreasing' if fvalue < 1 else 'increasing'
    else:  # two-sided
        pvalue = 2 * min(stats.f.sf(fvalue, df2, df1), stats.f.cdf(fvalue, df2, df1))
        ordering = 'increasing' if fvalue > 1 else 'decreasing'

    return fvalue, pvalue, ordering
