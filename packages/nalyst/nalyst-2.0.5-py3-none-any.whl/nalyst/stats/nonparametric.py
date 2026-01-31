"""
Nonparametric tests.
"""

from __future__ import annotations

from typing import Tuple, Optional, Literal
import numpy as np
from scipy import stats


def mannwhitneyu(
    x: np.ndarray,
    y: np.ndarray,
    alternative: Literal['two-sided', 'less', 'greater'] = 'two-sided',
    use_continuity: bool = True,
) -> Tuple[float, float]:
    """
    Mann-Whitney U test (Wilcoxon rank-sum test).

    Tests whether two independent samples come from the same distribution.

    Parameters
    ----------
    x : ndarray
        First sample.
    y : ndarray
        Second sample.
    alternative : {'two-sided', 'less', 'greater'}, default='two-sided'
        Alternative hypothesis.
    use_continuity : bool, default=True
        Whether to apply continuity correction.

    Returns
    -------
    statistic : float
        U statistic.
    pvalue : float
        P-value.

    Examples
    --------
    >>> from nalyst.stats import mannwhitneyu
    >>> u_stat, p = mannwhitneyu(group1, group2)
    """
    x = np.asarray(x).flatten()
    y = np.asarray(y).flatten()

    n1, n2 = len(x), len(y)

    # Combine and rank
    combined = np.concatenate([x, y])
    ranks = _rankdata(combined)

    # Sum of ranks for first sample
    R1 = np.sum(ranks[:n1])

    # U statistics
    U1 = n1 * n2 + n1 * (n1 + 1) / 2 - R1
    U2 = n1 * n2 - U1

    U = min(U1, U2)

    # Normal approximation for p-value
    mu = n1 * n2 / 2
    sigma = np.sqrt(n1 * n2 * (n1 + n2 + 1) / 12)

    # Continuity correction
    correction = 0.5 if use_continuity else 0

    if alternative == 'two-sided':
        z = (U - mu + correction) / sigma
        pvalue = 2 * stats.norm.sf(abs(z))
    elif alternative == 'less':
        z = (U1 - mu - correction) / sigma
        pvalue = stats.norm.cdf(z)
    else:  # greater
        z = (U1 - mu + correction) / sigma
        pvalue = stats.norm.sf(z)

    return U1, pvalue


def _rankdata(x: np.ndarray) -> np.ndarray:
    """Compute ranks with average for ties."""
    n = len(x)
    sorter = np.argsort(x)
    ranks = np.empty(n)
    ranks[sorter] = np.arange(1, n + 1)

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


def wilcoxon(
    x: np.ndarray,
    y: Optional[np.ndarray] = None,
    alternative: Literal['two-sided', 'less', 'greater'] = 'two-sided',
    zero_method: str = 'wilcox',
) -> Tuple[float, float]:
    """
    Wilcoxon signed-rank test.

    Tests whether paired samples come from the same distribution.

    Parameters
    ----------
    x : ndarray
        First sample (or differences if y is None).
    y : ndarray, optional
        Second sample (paired with x).
    alternative : {'two-sided', 'less', 'greater'}, default='two-sided'
        Alternative hypothesis.
    zero_method : str, default='wilcox'
        How to handle zero differences.

    Returns
    -------
    statistic : float
        W statistic.
    pvalue : float
        P-value.

    Examples
    --------
    >>> from nalyst.stats import wilcoxon
    >>> w_stat, p = wilcoxon(before, after)
    """
    x = np.asarray(x).flatten()

    if y is not None:
        y = np.asarray(y).flatten()
        if len(x) != len(y):
            raise ValueError("Samples must have equal length")
        d = x - y
    else:
        d = x

    # Remove zeros
    if zero_method == 'wilcox':
        d = d[d != 0]

    n = len(d)

    if n < 10:
        raise ValueError("Need at least 10 non-zero differences")

    # Rank absolute differences
    abs_d = np.abs(d)
    ranks = _rankdata(abs_d)

    # Sum of positive and negative ranks
    W_plus = np.sum(ranks[d > 0])
    W_minus = np.sum(ranks[d < 0])

    W = min(W_plus, W_minus)

    # Normal approximation
    mu = n * (n + 1) / 4
    sigma = np.sqrt(n * (n + 1) * (2 * n + 1) / 24)

    # Tie correction
    unique, counts = np.unique(abs_d, return_counts=True)
    tie_term = np.sum(counts**3 - counts) / 48
    sigma = np.sqrt(n * (n + 1) * (2 * n + 1) / 24 - tie_term)

    z = (W - mu) / sigma

    if alternative == 'two-sided':
        pvalue = 2 * stats.norm.sf(abs(z))
    elif alternative == 'less':
        pvalue = stats.norm.cdf(z)
    else:
        pvalue = stats.norm.sf(z)

    return W, pvalue


def kruskal(*args) -> Tuple[float, float]:
    """
    Kruskal-Wallis H-test.

    Non-parametric alternative to one-way ANOVA.
    Tests whether samples come from the same distribution.

    Parameters
    ----------
    *args : arrays
        Two or more independent samples.

    Returns
    -------
    statistic : float
        H statistic.
    pvalue : float
        P-value from chi-squared distribution.

    Examples
    --------
    >>> from nalyst.stats import kruskal
    >>> h_stat, p = kruskal(group1, group2, group3)
    """
    k = len(args)

    if k < 2:
        raise ValueError("Need at least 2 groups")

    samples = [np.asarray(a).flatten() for a in args]
    ns = [len(s) for s in samples]
    N = sum(ns)

    # Combine and rank
    combined = np.concatenate(samples)
    ranks = _rankdata(combined)

    # Split ranks back
    rank_sums = []
    idx = 0
    for n in ns:
        rank_sums.append(np.sum(ranks[idx:idx + n]))
        idx += n

    # H statistic
    H = 12 / (N * (N + 1)) * sum(R**2 / n for R, n in zip(rank_sums, ns)) - 3 * (N + 1)

    # Tie correction
    unique, counts = np.unique(combined, return_counts=True)
    tie_term = np.sum(counts**3 - counts)

    if tie_term > 0:
        H = H / (1 - tie_term / (N**3 - N))

    # P-value from chi-squared with k-1 df
    pvalue = stats.chi2.sf(H, k - 1)

    return H, pvalue


def friedmanchisquare(*args) -> Tuple[float, float]:
    """
    Friedman test for repeated measures.

    Non-parametric alternative to repeated measures ANOVA.

    Parameters
    ----------
    *args : arrays
        Repeated measurements for each subject.

    Returns
    -------
    statistic : float
        Friedman chi-squared statistic.
    pvalue : float
        P-value.

    Examples
    --------
    >>> from nalyst.stats import friedmanchisquare
    >>> stat, p = friedmanchisquare(time1, time2, time3)
    """
    k = len(args)

    if k < 3:
        raise ValueError("Need at least 3 repeated measurements")

    samples = [np.asarray(a).flatten() for a in args]
    n = len(samples[0])

    if not all(len(s) == n for s in samples):
        raise ValueError("All samples must have same length")

    # Create data matrix
    data = np.column_stack(samples)

    # Rank within each row (subject)
    ranks = np.zeros_like(data, dtype=float)
    for i in range(n):
        ranks[i] = _rankdata(data[i])

    # Sum of ranks for each treatment
    R = np.sum(ranks, axis=0)

    # Friedman statistic
    chi2 = 12 * n / (k * (k + 1)) * np.sum((R - n * (k + 1) / 2)**2)

    # P-value
    pvalue = stats.chi2.sf(chi2, k - 1)

    return chi2, pvalue


def ranksums(x: np.ndarray, y: np.ndarray) -> Tuple[float, float]:
    """
    Wilcoxon rank-sum test (equivalent to Mann-Whitney U).

    Parameters
    ----------
    x : ndarray
        First sample.
    y : ndarray
        Second sample.

    Returns
    -------
    statistic : float
        Z statistic.
    pvalue : float
        P-value.
    """
    x = np.asarray(x).flatten()
    y = np.asarray(y).flatten()

    n1, n2 = len(x), len(y)

    combined = np.concatenate([x, y])
    ranks = _rankdata(combined)

    R = np.sum(ranks[:n1])

    mu = n1 * (n1 + n2 + 1) / 2
    sigma = np.sqrt(n1 * n2 * (n1 + n2 + 1) / 12)

    z = (R - mu) / sigma
    pvalue = 2 * stats.norm.sf(abs(z))

    return z, pvalue
