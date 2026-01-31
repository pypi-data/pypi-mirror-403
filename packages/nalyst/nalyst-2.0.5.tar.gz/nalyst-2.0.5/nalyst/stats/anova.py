"""
ANOVA and related tests.
"""

from __future__ import annotations

from typing import Tuple, Dict, Any, List, Optional
import numpy as np
from scipy import stats


def f_oneway(*args) -> Tuple[float, float]:
    """
    One-way ANOVA.

    Tests whether the means of multiple groups are equal.

    Parameters
    ----------
    *args : arrays
        Sample data for each group.

    Returns
    -------
    statistic : float
        F statistic.
    pvalue : float
        P-value.

    Examples
    --------
    >>> from nalyst.stats import f_oneway
    >>> f_stat, p = f_oneway(group1, group2, group3)
    """
    k = len(args)

    if k < 2:
        raise ValueError("Need at least 2 groups")

    samples = [np.asarray(a).flatten() for a in args]
    ns = [len(s) for s in samples]
    N = sum(ns)

    # Grand mean
    all_data = np.concatenate(samples)
    grand_mean = np.mean(all_data)

    # Group means
    group_means = [np.mean(s) for s in samples]

    # Between-group sum of squares
    ss_between = sum(n * (m - grand_mean)**2 for n, m in zip(ns, group_means))

    # Within-group sum of squares
    ss_within = sum(np.sum((s - m)**2) for s, m in zip(samples, group_means))

    # Degrees of freedom
    df_between = k - 1
    df_within = N - k

    # Mean squares
    ms_between = ss_between / df_between
    ms_within = ss_within / df_within

    # F statistic
    F = ms_between / ms_within

    # P-value
    pvalue = stats.f.sf(F, df_between, df_within)

    return F, pvalue


def anova_lm(y: np.ndarray, X: np.ndarray, groups: Optional[np.ndarray] = None) -> Dict[str, Any]:
    """
    ANOVA table from linear model.

    Parameters
    ----------
    y : ndarray
        Dependent variable.
    X : ndarray
        Design matrix.
    groups : ndarray, optional
        Group labels for one-way ANOVA.

    Returns
    -------
    result : dict
        ANOVA table with SS, df, MS, F, and p-value.

    Examples
    --------
    >>> from nalyst.stats import anova_lm
    >>> result = anova_lm(y, X)
    """
    y = np.asarray(y).flatten()
    X = np.asarray(X)

    if X.ndim == 1:
        X = X.reshape(-1, 1)

    n = len(y)
    p = X.shape[1]

    # Add constant if not present
    if not np.allclose(X[:, 0], 1):
        X = np.column_stack([np.ones(n), X])
        p += 1

    # OLS fit
    beta = np.linalg.lstsq(X, y, rcond=None)[0]
    y_pred = X @ beta
    resid = y - y_pred

    # Sums of squares
    y_mean = np.mean(y)
    ss_total = np.sum((y - y_mean)**2)
    ss_resid = np.sum(resid**2)
    ss_model = ss_total - ss_resid

    # Degrees of freedom
    df_model = p - 1
    df_resid = n - p
    df_total = n - 1

    # Mean squares
    ms_model = ss_model / df_model if df_model > 0 else 0
    ms_resid = ss_resid / df_resid if df_resid > 0 else 0

    # F statistic
    F = ms_model / ms_resid if ms_resid > 0 else 0
    pvalue = stats.f.sf(F, df_model, df_resid)

    return {
        'ss_model': ss_model,
        'ss_resid': ss_resid,
        'ss_total': ss_total,
        'df_model': df_model,
        'df_resid': df_resid,
        'df_total': df_total,
        'ms_model': ms_model,
        'ms_resid': ms_resid,
        'f_statistic': F,
        'p_value': pvalue,
        'r_squared': ss_model / ss_total if ss_total > 0 else 0,
    }


def tukey_hsd(*args, alpha: float = 0.05) -> Dict[str, Any]:
    """
    Tukey's Honest Significant Difference test.

    Post-hoc test for pairwise comparisons after ANOVA.

    Parameters
    ----------
    *args : arrays
        Sample data for each group.
    alpha : float, default=0.05
        Significance level.

    Returns
    -------
    result : dict
        Pairwise comparisons with mean differences and significance.

    Examples
    --------
    >>> from nalyst.stats import tukey_hsd
    >>> result = tukey_hsd(group1, group2, group3)
    >>> print(result['comparisons'])
    """
    k = len(args)
    samples = [np.asarray(a).flatten() for a in args]
    ns = [len(s) for s in samples]
    N = sum(ns)

    # Group means
    means = [np.mean(s) for s in samples]

    # MSE (pooled variance)
    ss_within = sum(np.sum((s - m)**2) for s, m in zip(samples, means))
    df_within = N - k
    mse = ss_within / df_within

    # Pairwise comparisons
    comparisons = []

    for i in range(k):
        for j in range(i + 1, k):
            diff = means[i] - means[j]
            se = np.sqrt(mse * (1/ns[i] + 1/ns[j]) / 2)
            q = abs(diff) / se

            # Critical value from studentized range distribution
            # Using approximation
            q_crit = stats.studentized_range.ppf(1 - alpha, k, df_within)

            significant = q > q_crit

            comparisons.append({
                'group1': i,
                'group2': j,
                'mean_diff': diff,
                'std_err': se,
                'q_statistic': q,
                'q_critical': q_crit,
                'significant': significant,
            })

    return {
        'comparisons': comparisons,
        'mse': mse,
        'df': df_within,
        'alpha': alpha,
    }


def levene(*args, center: str = 'median') -> Tuple[float, float]:
    """
    Levene's test for equality of variances.

    Parameters
    ----------
    *args : arrays
        Sample data for each group.
    center : str, default='median'
        Which center to use: 'mean', 'median', or 'trimmed'.

    Returns
    -------
    statistic : float
        Levene statistic.
    pvalue : float
        P-value.

    Examples
    --------
    >>> from nalyst.stats import levene
    >>> stat, p = levene(group1, group2, group3)
    """
    k = len(args)
    samples = [np.asarray(a).flatten() for a in args]

    # Compute absolute deviations from center
    if center == 'median':
        centers = [np.median(s) for s in samples]
    elif center == 'trimmed':
        centers = [stats.trim_mean(s, 0.1) for s in samples]
    else:
        centers = [np.mean(s) for s in samples]

    z_samples = [np.abs(s - c) for s, c in zip(samples, centers)]

    # Apply ANOVA on absolute deviations
    return f_oneway(*z_samples)


def bartlett(*args) -> Tuple[float, float]:
    """
    Bartlett's test for equality of variances.

    More sensitive than Levene but assumes normality.

    Parameters
    ----------
    *args : arrays
        Sample data for each group.

    Returns
    -------
    statistic : float
        Bartlett statistic.
    pvalue : float
        P-value.

    Examples
    --------
    >>> from nalyst.stats import bartlett
    >>> stat, p = bartlett(group1, group2, group3)
    """
    k = len(args)
    samples = [np.asarray(a).flatten() for a in args]
    ns = [len(s) for s in samples]
    N = sum(ns)

    # Sample variances
    vars = [np.var(s, ddof=1) for s in samples]

    # Pooled variance
    sp2 = sum((n - 1) * v for n, v in zip(ns, vars)) / (N - k)

    # Bartlett statistic
    numerator = (N - k) * np.log(sp2) - sum((n - 1) * np.log(v) for n, v in zip(ns, vars))

    # Correction factor
    c = 1 + (1 / (3 * (k - 1))) * (sum(1/(n-1) for n in ns) - 1/(N-k))

    T = numerator / c

    # P-value from chi-squared
    pvalue = stats.chi2.sf(T, k - 1)

    return T, pvalue
