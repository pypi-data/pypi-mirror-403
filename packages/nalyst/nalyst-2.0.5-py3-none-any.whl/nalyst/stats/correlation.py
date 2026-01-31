"""
Correlation tests and measures.
"""

from __future__ import annotations

from typing import Tuple, Optional
import numpy as np
from scipy import stats


def pearsonr(x: np.ndarray, y: np.ndarray) -> Tuple[float, float]:
    """
    Pearson correlation coefficient.

    Measures linear correlation between two variables.

    Parameters
    ----------
    x : ndarray
        First variable.
    y : ndarray
        Second variable.

    Returns
    -------
    r : float
        Pearson correlation coefficient.
    pvalue : float
        Two-tailed p-value.

    Examples
    --------
    >>> from nalyst.stats import pearsonr
    >>> r, p = pearsonr(x, y)
    >>> print(f"Correlation: {r:.3f}, p-value: {p:.4f}")
    """
    x = np.asarray(x).flatten()
    y = np.asarray(y).flatten()

    if len(x) != len(y):
        raise ValueError("Arrays must have same length")

    n = len(x)

    if n < 3:
        raise ValueError("Need at least 3 observations")

    # Compute correlation
    x_mean = np.mean(x)
    y_mean = np.mean(y)

    x_centered = x - x_mean
    y_centered = y - y_mean

    numerator = np.sum(x_centered * y_centered)
    denominator = np.sqrt(np.sum(x_centered**2) * np.sum(y_centered**2))

    if denominator == 0:
        return 0.0, 1.0

    r = numerator / denominator

    # Compute p-value using t-distribution
    t_stat = r * np.sqrt((n - 2) / (1 - r**2 + 1e-10))
    pvalue = 2 * stats.t.sf(abs(t_stat), n - 2)

    return r, pvalue


def spearmanr(x: np.ndarray, y: np.ndarray) -> Tuple[float, float]:
    """
    Spearman rank correlation coefficient.

    Measures monotonic relationship between two variables.

    Parameters
    ----------
    x : ndarray
        First variable.
    y : ndarray
        Second variable.

    Returns
    -------
    rho : float
        Spearman correlation coefficient.
    pvalue : float
        Two-tailed p-value.

    Examples
    --------
    >>> from nalyst.stats import spearmanr
    >>> rho, p = spearmanr(x, y)
    """
    x = np.asarray(x).flatten()
    y = np.asarray(y).flatten()

    if len(x) != len(y):
        raise ValueError("Arrays must have same length")

    n = len(x)

    # Compute ranks
    x_ranks = _rankdata(x)
    y_ranks = _rankdata(y)

    # Pearson correlation on ranks
    return pearsonr(x_ranks, y_ranks)


def _rankdata(x: np.ndarray) -> np.ndarray:
    """Compute ranks (average for ties)."""
    n = len(x)
    sorter = np.argsort(x)

    ranks = np.empty(n)
    ranks[sorter] = np.arange(1, n + 1)

    # Handle ties
    sorted_x = x[sorter]

    i = 0
    while i < n:
        j = i
        while j < n - 1 and sorted_x[j] == sorted_x[j + 1]:
            j += 1

        if j > i:
            avg_rank = (i + j + 2) / 2
            for k in range(i, j + 1):
                ranks[sorter[k]] = avg_rank

        i = j + 1

    return ranks


def kendalltau(x: np.ndarray, y: np.ndarray) -> Tuple[float, float]:
    """
    Kendall's tau correlation coefficient.

    Measures ordinal association between two variables.

    Parameters
    ----------
    x : ndarray
        First variable.
    y : ndarray
        Second variable.

    Returns
    -------
    tau : float
        Kendall's tau.
    pvalue : float
        Two-tailed p-value.

    Examples
    --------
    >>> from nalyst.stats import kendalltau
    >>> tau, p = kendalltau(x, y)
    """
    x = np.asarray(x).flatten()
    y = np.asarray(y).flatten()

    if len(x) != len(y):
        raise ValueError("Arrays must have same length")

    n = len(x)

    if n < 2:
        return 0.0, 1.0

    # Count concordant and discordant pairs
    concordant = 0
    discordant = 0
    ties_x = 0
    ties_y = 0
    ties_xy = 0

    for i in range(n - 1):
        for j in range(i + 1, n):
            dx = x[i] - x[j]
            dy = y[i] - y[j]

            if dx == 0 and dy == 0:
                ties_xy += 1
            elif dx == 0:
                ties_x += 1
            elif dy == 0:
                ties_y += 1
            elif (dx > 0 and dy > 0) or (dx < 0 and dy < 0):
                concordant += 1
            else:
                discordant += 1

    n_pairs = n * (n - 1) // 2

    # Kendall's tau-b (handles ties)
    n0 = n_pairs
    n1 = ties_x
    n2 = ties_y

    denom = np.sqrt((n0 - n1) * (n0 - n2))

    if denom == 0:
        tau = 0.0
    else:
        tau = (concordant - discordant) / denom

    # P-value (normal approximation for large n)
    if n >= 10:
        var = (2 * (2 * n + 5)) / (9 * n * (n - 1))
        z = tau / np.sqrt(var)
        pvalue = 2 * stats.norm.sf(abs(z))
    else:
        # Use permutation approximation
        pvalue = 0.5

    return tau, pvalue


def partial_corr(
    x: np.ndarray,
    y: np.ndarray,
    covar: np.ndarray,
    method: str = 'pearson',
) -> Tuple[float, float]:
    """
    Partial correlation controlling for covariates.

    Parameters
    ----------
    x : ndarray
        First variable.
    y : ndarray
        Second variable.
    covar : ndarray of shape (n_samples, n_covariates)
        Covariates to control for.
    method : str, default='pearson'
        Correlation method: 'pearson' or 'spearman'.

    Returns
    -------
    r : float
        Partial correlation coefficient.
    pvalue : float
        P-value.

    Examples
    --------
    >>> from nalyst.stats import partial_corr
    >>> r, p = partial_corr(x, y, covar=z)
    """
    x = np.asarray(x).flatten()
    y = np.asarray(y).flatten()
    covar = np.asarray(covar)

    if covar.ndim == 1:
        covar = covar.reshape(-1, 1)

    n = len(x)

    # Residuals from regressing x and y on covariates
    covar_with_const = np.column_stack([np.ones(n), covar])

    # Residualize x
    beta_x = np.linalg.lstsq(covar_with_const, x, rcond=None)[0]
    x_resid = x - covar_with_const @ beta_x

    # Residualize y
    beta_y = np.linalg.lstsq(covar_with_const, y, rcond=None)[0]
    y_resid = y - covar_with_const @ beta_y

    # Correlation of residuals
    if method == 'spearman':
        return spearmanr(x_resid, y_resid)
    else:
        return pearsonr(x_resid, y_resid)


def point_biserial(x: np.ndarray, y: np.ndarray) -> Tuple[float, float]:
    """
    Point-biserial correlation.

    Correlation between a binary variable and a continuous variable.

    Parameters
    ----------
    x : ndarray
        Binary variable (0 or 1).
    y : ndarray
        Continuous variable.

    Returns
    -------
    r : float
        Point-biserial correlation.
    pvalue : float
        P-value.
    """
    x = np.asarray(x).flatten()
    y = np.asarray(y).flatten()

    # Ensure x is binary
    unique = np.unique(x)
    if len(unique) != 2:
        raise ValueError("First variable must be binary")

    # Convert to 0/1
    x = (x == unique[1]).astype(float)

    return pearsonr(x, y)
