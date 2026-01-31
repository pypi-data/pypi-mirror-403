"""
Hypothesis tests: t-tests and z-tests.
"""

from __future__ import annotations

from typing import Tuple, Optional, Literal, Dict, Any
import numpy as np
from scipy import stats


def ttest_1samp(
    x: np.ndarray,
    popmean: float,
    alternative: Literal['two-sided', 'less', 'greater'] = 'two-sided',
) -> Tuple[float, float]:
    """
    One-sample t-test.

    Test whether the mean of a sample differs from a population mean.

    Parameters
    ----------
    x : ndarray
        Sample observations.
    popmean : float
        Expected population mean.
    alternative : {'two-sided', 'less', 'greater'}, default='two-sided'
        Alternative hypothesis.

    Returns
    -------
    statistic : float
        T-statistic.
    pvalue : float
        P-value.

    Examples
    --------
    >>> from nalyst.stats import ttest_1samp
    >>> t_stat, p_val = ttest_1samp(sample, popmean=100)
    """
    x = np.asarray(x).flatten()
    n = len(x)

    mean = np.mean(x)
    se = np.std(x, ddof=1) / np.sqrt(n)

    t_stat = (mean - popmean) / se
    df = n - 1

    if alternative == 'two-sided':
        pvalue = 2 * stats.t.sf(abs(t_stat), df)
    elif alternative == 'less':
        pvalue = stats.t.cdf(t_stat, df)
    else:  # greater
        pvalue = stats.t.sf(t_stat, df)

    return t_stat, pvalue


def ttest_ind(
    x: np.ndarray,
    y: np.ndarray,
    equal_var: bool = True,
    alternative: Literal['two-sided', 'less', 'greater'] = 'two-sided',
) -> Tuple[float, float]:
    """
    Independent samples t-test.

    Test whether the means of two independent samples are equal.

    Parameters
    ----------
    x : ndarray
        First sample.
    y : ndarray
        Second sample.
    equal_var : bool, default=True
        If True, assume equal population variances (Student's t-test).
        If False, use Welch's t-test.
    alternative : {'two-sided', 'less', 'greater'}, default='two-sided'
        Alternative hypothesis.

    Returns
    -------
    statistic : float
        T-statistic.
    pvalue : float
        P-value.

    Examples
    --------
    >>> from nalyst.stats import ttest_ind
    >>> t_stat, p_val = ttest_ind(group1, group2)
    """
    x = np.asarray(x).flatten()
    y = np.asarray(y).flatten()

    n1, n2 = len(x), len(y)
    mean1, mean2 = np.mean(x), np.mean(y)
    var1, var2 = np.var(x, ddof=1), np.var(y, ddof=1)

    if equal_var:
        # Pooled variance
        pooled_var = ((n1 - 1) * var1 + (n2 - 1) * var2) / (n1 + n2 - 2)
        se = np.sqrt(pooled_var * (1/n1 + 1/n2))
        df = n1 + n2 - 2
    else:
        # Welch's t-test
        se = np.sqrt(var1/n1 + var2/n2)
        # Welch-Satterthwaite degrees of freedom
        df = (var1/n1 + var2/n2)**2 / (
            (var1/n1)**2 / (n1-1) + (var2/n2)**2 / (n2-1)
        )

    t_stat = (mean1 - mean2) / se

    if alternative == 'two-sided':
        pvalue = 2 * stats.t.sf(abs(t_stat), df)
    elif alternative == 'less':
        pvalue = stats.t.cdf(t_stat, df)
    else:  # greater
        pvalue = stats.t.sf(t_stat, df)

    return t_stat, pvalue


def ttest_rel(
    x: np.ndarray,
    y: np.ndarray,
    alternative: Literal['two-sided', 'less', 'greater'] = 'two-sided',
) -> Tuple[float, float]:
    """
    Paired samples t-test.

    Test whether the mean difference of paired samples is zero.

    Parameters
    ----------
    x : ndarray
        First sample.
    y : ndarray
        Second sample (paired with x).
    alternative : {'two-sided', 'less', 'greater'}, default='two-sided'
        Alternative hypothesis.

    Returns
    -------
    statistic : float
        T-statistic.
    pvalue : float
        P-value.

    Examples
    --------
    >>> from nalyst.stats import ttest_rel
    >>> t_stat, p_val = ttest_rel(before, after)
    """
    x = np.asarray(x).flatten()
    y = np.asarray(y).flatten()

    if len(x) != len(y):
        raise ValueError("Samples must have equal length for paired t-test")

    d = x - y
    return ttest_1samp(d, popmean=0, alternative=alternative)


def ztest(
    x: np.ndarray,
    value: float = 0,
    sigma: Optional[float] = None,
    alternative: Literal['two-sided', 'less', 'greater'] = 'two-sided',
) -> Tuple[float, float]:
    """
    One-sample z-test.

    Test whether the mean differs from a specified value.

    Parameters
    ----------
    x : ndarray
        Sample observations.
    value : float, default=0
        Hypothesized population mean.
    sigma : float, optional
        Known population standard deviation. If None, uses sample std.
    alternative : {'two-sided', 'less', 'greater'}, default='two-sided'
        Alternative hypothesis.

    Returns
    -------
    statistic : float
        Z-statistic.
    pvalue : float
        P-value.

    Examples
    --------
    >>> from nalyst.stats import ztest
    >>> z_stat, p_val = ztest(sample, value=100, sigma=15)
    """
    x = np.asarray(x).flatten()
    n = len(x)

    mean = np.mean(x)

    if sigma is None:
        sigma = np.std(x, ddof=1)

    se = sigma / np.sqrt(n)
    z_stat = (mean - value) / se

    if alternative == 'two-sided':
        pvalue = 2 * stats.norm.sf(abs(z_stat))
    elif alternative == 'less':
        pvalue = stats.norm.cdf(z_stat)
    else:  # greater
        pvalue = stats.norm.sf(z_stat)

    return z_stat, pvalue


def ztest_ind(
    x: np.ndarray,
    y: np.ndarray,
    sigma1: Optional[float] = None,
    sigma2: Optional[float] = None,
    alternative: Literal['two-sided', 'less', 'greater'] = 'two-sided',
) -> Tuple[float, float]:
    """
    Two-sample z-test.

    Test whether two independent samples have equal means.

    Parameters
    ----------
    x : ndarray
        First sample.
    y : ndarray
        Second sample.
    sigma1 : float, optional
        Known population std of first sample.
    sigma2 : float, optional
        Known population std of second sample.
    alternative : {'two-sided', 'less', 'greater'}, default='two-sided'
        Alternative hypothesis.

    Returns
    -------
    statistic : float
        Z-statistic.
    pvalue : float
        P-value.
    """
    x = np.asarray(x).flatten()
    y = np.asarray(y).flatten()

    n1, n2 = len(x), len(y)
    mean1, mean2 = np.mean(x), np.mean(y)

    if sigma1 is None:
        sigma1 = np.std(x, ddof=1)
    if sigma2 is None:
        sigma2 = np.std(y, ddof=1)

    se = np.sqrt(sigma1**2/n1 + sigma2**2/n2)
    z_stat = (mean1 - mean2) / se

    if alternative == 'two-sided':
        pvalue = 2 * stats.norm.sf(abs(z_stat))
    elif alternative == 'less':
        pvalue = stats.norm.cdf(z_stat)
    else:  # greater
        pvalue = stats.norm.sf(z_stat)

    return z_stat, pvalue
