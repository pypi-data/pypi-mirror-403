"""
Contingency table analysis.
"""

from __future__ import annotations

from typing import Tuple, Dict, Any, Optional
import numpy as np
from scipy import stats


def chi2_contingency(
    observed: np.ndarray,
    correction: bool = True,
    lambda_: Optional[float] = None,
) -> Tuple[float, float, int, np.ndarray]:
    """
    Chi-square test of independence on contingency table.

    Parameters
    ----------
    observed : ndarray
        Contingency table (frequency table).
    correction : bool, default=True
        Apply Yates' continuity correction for 2x2 tables.
    lambda_ : float, optional
        Exponent for power divergence statistic (1 = chi-square).

    Returns
    -------
    chi2 : float
        Chi-squared test statistic.
    pvalue : float
        P-value.
    dof : int
        Degrees of freedom.
    expected : ndarray
        Expected frequencies.

    Examples
    --------
    >>> from nalyst.stats import chi2_contingency
    >>> table = [[10, 20], [30, 40]]
    >>> chi2, p, dof, expected = chi2_contingency(table)
    """
    observed = np.asarray(observed, dtype=float)

    if observed.ndim != 2:
        raise ValueError("Expected 2D contingency table")

    nrows, ncols = observed.shape

    # Marginal sums
    row_sums = observed.sum(axis=1)
    col_sums = observed.sum(axis=0)
    total = observed.sum()

    # Expected frequencies
    expected = np.outer(row_sums, col_sums) / total

    # Degrees of freedom
    dof = (nrows - 1) * (ncols - 1)

    # Chi-squared statistic
    if lambda_ is None or lambda_ == 1:
        # Standard chi-squared
        if correction and nrows == 2 and ncols == 2:
            # Yates' correction
            diff = np.abs(observed - expected) - 0.5
            diff = np.maximum(diff, 0)
            chi2 = np.sum(diff**2 / expected)
        else:
            chi2 = np.sum((observed - expected)**2 / expected)
    else:
        # Power divergence
        ratio = observed / expected
        if lambda_ == 0:
            chi2 = 2 * np.sum(observed * np.log(ratio))
        else:
            chi2 = 2 / (lambda_ * (lambda_ + 1)) * np.sum(observed * (ratio**lambda_ - 1))

    # P-value
    pvalue = stats.chi2.sf(chi2, dof)

    return chi2, pvalue, dof, expected


def fisher_exact(table: np.ndarray, alternative: str = 'two-sided') -> Tuple[float, float]:
    """
    Fisher's exact test for 2x2 contingency tables.

    Parameters
    ----------
    table : ndarray of shape (2, 2)
        2x2 contingency table.
    alternative : str, default='two-sided'
        Alternative hypothesis: 'two-sided', 'less', 'greater'.

    Returns
    -------
    odds_ratio : float
        Odds ratio.
    pvalue : float
        P-value.

    Examples
    --------
    >>> from nalyst.stats import fisher_exact
    >>> table = [[8, 2], [1, 9]]
    >>> odds_ratio, p = fisher_exact(table)
    """
    table = np.asarray(table)

    if table.shape != (2, 2):
        raise ValueError("Fisher exact test requires 2x2 table")

    a, b = table[0]
    c, d = table[1]

    # Odds ratio
    if b * c == 0:
        oddsratio = np.inf if a * d > 0 else 0.0
    else:
        oddsratio = (a * d) / (b * c)

    # Marginals
    row1 = a + b
    row2 = c + d
    col1 = a + c
    col2 = b + d
    n = a + b + c + d

    # Hypergeometric distribution for p-value
    lo = max(0, row1 - col2)
    hi = min(row1, col1)

    # Probability of observed configuration
    from scipy.special import comb

    def hypergeom_pmf(x):
        return comb(col1, x) * comb(col2, row1 - x) / comb(n, row1)

    p_obs = hypergeom_pmf(a)

    if alternative == 'two-sided':
        pvalue = sum(hypergeom_pmf(x) for x in range(lo, hi + 1)
                    if hypergeom_pmf(x) <= p_obs + 1e-10)
    elif alternative == 'less':
        pvalue = sum(hypergeom_pmf(x) for x in range(lo, a + 1))
    else:  # greater
        pvalue = sum(hypergeom_pmf(x) for x in range(a, hi + 1))

    return oddsratio, min(1.0, pvalue)


def cramers_v(table: np.ndarray) -> float:
    """
    Cramr's V measure of association.

    Effect size measure for chi-squared test.

    Parameters
    ----------
    table : ndarray
        Contingency table.

    Returns
    -------
    v : float
        Cramr's V (0 to 1).

    Examples
    --------
    >>> from nalyst.stats import cramers_v
    >>> v = cramers_v([[10, 20], [30, 40]])
    """
    table = np.asarray(table)

    chi2, _, _, _ = chi2_contingency(table, correction=False)

    n = table.sum()
    nrows, ncols = table.shape

    v = np.sqrt(chi2 / (n * (min(nrows, ncols) - 1)))

    return v


def odds_ratio(table: np.ndarray, alpha: float = 0.05) -> Dict[str, Any]:
    """
    Compute odds ratio with confidence interval.

    Parameters
    ----------
    table : ndarray of shape (2, 2)
        2x2 contingency table.
    alpha : float, default=0.05
        Significance level for CI.

    Returns
    -------
    result : dict
        Odds ratio, confidence interval, and related statistics.

    Examples
    --------
    >>> from nalyst.stats import odds_ratio
    >>> result = odds_ratio([[10, 20], [30, 40]])
    """
    table = np.asarray(table)

    if table.shape != (2, 2):
        raise ValueError("Odds ratio requires 2x2 table")

    a, b = table[0]
    c, d = table[1]

    # Odds ratio
    if b * c == 0:
        or_val = np.inf if a * d > 0 else 0.0
        log_or = np.inf
        se_log_or = np.inf
    else:
        or_val = (a * d) / (b * c)
        log_or = np.log(or_val)
        se_log_or = np.sqrt(1/a + 1/b + 1/c + 1/d)

    # Confidence interval
    z = stats.norm.ppf(1 - alpha/2)

    if np.isfinite(se_log_or):
        ci_lower = np.exp(log_or - z * se_log_or)
        ci_upper = np.exp(log_or + z * se_log_or)
    else:
        ci_lower = 0.0
        ci_upper = np.inf

    # Risk ratio
    risk1 = a / (a + b) if (a + b) > 0 else 0
    risk2 = c / (c + d) if (c + d) > 0 else 0

    if risk2 > 0:
        risk_ratio = risk1 / risk2
    else:
        risk_ratio = np.inf if risk1 > 0 else 1.0

    return {
        'odds_ratio': or_val,
        'log_odds_ratio': log_or,
        'se_log_or': se_log_or,
        'ci_lower': ci_lower,
        'ci_upper': ci_upper,
        'risk_ratio': risk_ratio,
        'risk1': risk1,
        'risk2': risk2,
    }
