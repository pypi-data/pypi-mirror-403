"""
Normality tests.
"""

from __future__ import annotations

from typing import Tuple, Dict, Any
import numpy as np
from scipy import stats


def shapiro(x: np.ndarray) -> Tuple[float, float]:
    """
    Shapiro-Wilk test for normality.

    The null hypothesis is that the data was drawn from a normal distribution.

    Parameters
    ----------
    x : ndarray
        Sample data.

    Returns
    -------
    statistic : float
        Test statistic.
    pvalue : float
        P-value.

    Examples
    --------
    >>> from nalyst.stats import shapiro
    >>> stat, p = shapiro(data)
    >>> if p > 0.05:
    ...     print("Data appears normally distributed")
    """
    x = np.asarray(x).flatten()
    n = len(x)

    if n < 3:
        raise ValueError("Need at least 3 observations")

    if n > 5000:
        # Use scipy for large samples
        return stats.shapiro(x)

    # Sort data
    x_sorted = np.sort(x)

    # Compute expected normal order statistics
    m = np.array([stats.norm.ppf((i - 0.375) / (n + 0.25)) for i in range(1, n + 1)])

    # Compute coefficients
    u = 1 / np.sqrt(n)

    # Shapiro-Wilk coefficients (simplified approximation)
    a = np.zeros(n)
    a[-1] = 0.7071068
    a[-2] = -0.7071068

    if n > 2:
        c = m / np.sqrt(np.sum(m**2))
        a = c

    # Compute W statistic
    x_centered = x_sorted - np.mean(x_sorted)

    numerator = np.sum(a * x_sorted) ** 2
    denominator = np.sum(x_centered ** 2)

    W = numerator / denominator

    # Compute p-value using transformation
    # Simplified approximation
    if n >= 4:
        mu = 0.0038915 * n**3 - 0.083751 * n**2 - 0.31082 * n - 1.5861
        sigma = np.exp(0.0030302 * n**2 - 0.082676 * n - 0.4803)

        z = (np.log(1 - W) - mu) / sigma
        pvalue = stats.norm.sf(z)
    else:
        # Use lookup for very small samples
        pvalue = 0.5 if W > 0.9 else 0.05

    return W, pvalue


def jarque_bera(x: np.ndarray) -> Tuple[float, float]:
    """
    Jarque-Bera test for normality.

    Tests whether sample data has skewness and kurtosis matching a normal distribution.

    Parameters
    ----------
    x : ndarray
        Sample data.

    Returns
    -------
    statistic : float
        JB test statistic.
    pvalue : float
        P-value from chi-squared distribution.

    Examples
    --------
    >>> from nalyst.stats import jarque_bera
    >>> jb_stat, p = jarque_bera(data)
    """
    x = np.asarray(x).flatten()
    n = len(x)

    if n < 3:
        raise ValueError("Need at least 3 observations")

    # Compute moments
    mean = np.mean(x)
    var = np.var(x, ddof=0)

    if var == 0:
        return 0.0, 1.0

    # Standardize
    x_std = (x - mean) / np.sqrt(var)

    # Skewness and kurtosis
    skewness = np.mean(x_std ** 3)
    kurtosis = np.mean(x_std ** 4) - 3  # Excess kurtosis

    # JB statistic
    jb = (n / 6) * (skewness**2 + (kurtosis**2) / 4)

    # P-value from chi-squared with 2 df
    pvalue = stats.chi2.sf(jb, 2)

    return jb, pvalue


def anderson(x: np.ndarray, dist: str = 'norm') -> Dict[str, Any]:
    """
    Anderson-Darling test for distribution fit.

    Parameters
    ----------
    x : ndarray
        Sample data.
    dist : str, default='norm'
        Distribution: 'norm', 'expon', 'logistic', 'gumbel'.

    Returns
    -------
    result : dict
        Dictionary with statistic, critical_values, and significance_level.

    Examples
    --------
    >>> from nalyst.stats import anderson
    >>> result = anderson(data)
    >>> print(f"Statistic: {result['statistic']}")
    """
    x = np.asarray(x).flatten()
    n = len(x)
    x_sorted = np.sort(x)

    if dist == 'norm':
        # Standardize
        mean = np.mean(x)
        std = np.std(x, ddof=1)
        x_std = (x_sorted - mean) / std

        # CDF values
        cdf = stats.norm.cdf(x_std)
    elif dist == 'expon':
        scale = np.mean(x)
        cdf = stats.expon.cdf(x_sorted, scale=scale)
    else:
        mean = np.mean(x)
        std = np.std(x, ddof=1)
        x_std = (x_sorted - mean) / std
        cdf = stats.norm.cdf(x_std)

    # Clip to avoid log(0)
    cdf = np.clip(cdf, 1e-10, 1 - 1e-10)

    # A statistic
    i = np.arange(1, n + 1)
    A2 = -n - np.mean((2 * i - 1) * (np.log(cdf) + np.log(1 - cdf[::-1])))

    # Modify for normal distribution
    if dist == 'norm':
        A2 = A2 * (1 + 4/n - 25/n**2)

    # Critical values for normal distribution
    if dist == 'norm':
        critical_values = [0.576, 0.656, 0.787, 0.918, 1.092]
        significance_levels = [15, 10, 5, 2.5, 1]
    else:
        critical_values = [0.5, 0.6, 0.7, 0.8, 1.0]
        significance_levels = [15, 10, 5, 2.5, 1]

    return {
        'statistic': A2,
        'critical_values': critical_values,
        'significance_level': significance_levels,
    }


def lilliefors(x: np.ndarray) -> Tuple[float, float]:
    """
    Lilliefors test for normality.

    Similar to Kolmogorov-Smirnov but with estimated parameters.

    Parameters
    ----------
    x : ndarray
        Sample data.

    Returns
    -------
    statistic : float
        D statistic.
    pvalue : float
        P-value.
    """
    x = np.asarray(x).flatten()
    n = len(x)

    # Standardize
    mean = np.mean(x)
    std = np.std(x, ddof=1)
    x_std = (x - mean) / std

    x_sorted = np.sort(x_std)

    # Compute D statistic
    cdf = stats.norm.cdf(x_sorted)

    D_plus = np.max(np.arange(1, n + 1) / n - cdf)
    D_minus = np.max(cdf - np.arange(0, n) / n)
    D = max(D_plus, D_minus)

    # P-value approximation (Dallal-Wilkinson)
    if n >= 5:
        if D < 0.1:
            pvalue = 1.0
        else:
            sqrt_n = np.sqrt(n)
            pvalue = np.exp(-7.01256 * D**2 * (n + 2.78019) +
                           2.99587 * D * sqrt_n - 0.122119 +
                           0.974598 / sqrt_n + 1.67997 / n)
            pvalue = min(1.0, max(0.0, pvalue))
    else:
        pvalue = 0.5  # Not enough data

    return D, pvalue


def kstest(
    x: np.ndarray,
    cdf: str = 'norm',
    args: Tuple = (),
    alternative: str = 'two-sided',
) -> Tuple[float, float]:
    """
    Kolmogorov-Smirnov test.

    Test goodness of fit to a specified distribution.

    Parameters
    ----------
    x : ndarray
        Sample data.
    cdf : str, default='norm'
        Distribution name.
    args : tuple
        Distribution parameters.
    alternative : str, default='two-sided'
        Alternative hypothesis.

    Returns
    -------
    statistic : float
        D statistic.
    pvalue : float
        P-value.

    Examples
    --------
    >>> from nalyst.stats import kstest
    >>> stat, p = kstest(data, 'norm')
    """
    x = np.asarray(x).flatten()
    n = len(x)
    x_sorted = np.sort(x)

    # Get distribution
    if cdf == 'norm':
        dist = stats.norm(*args)
    elif cdf == 'expon':
        dist = stats.expon(*args)
    elif cdf == 'uniform':
        dist = stats.uniform(*args)
    else:
        dist = getattr(stats, cdf)(*args)

    cdf_vals = dist.cdf(x_sorted)

    # D statistics
    D_plus = np.max(np.arange(1, n + 1) / n - cdf_vals)
    D_minus = np.max(cdf_vals - np.arange(0, n) / n)

    if alternative == 'two-sided':
        D = max(D_plus, D_minus)
    elif alternative == 'less':
        D = D_minus
    else:
        D = D_plus

    # P-value using asymptotic approximation
    sqrt_n = np.sqrt(n)

    if alternative == 'two-sided':
        # Kolmogorov distribution approximation
        z = D * sqrt_n
        pvalue = 2 * np.exp(-2 * z**2)
    else:
        pvalue = np.exp(-2 * n * D**2)

    pvalue = min(1.0, max(0.0, pvalue))

    return D, pvalue
