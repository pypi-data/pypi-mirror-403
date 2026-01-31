"""
Statistical power analysis.
"""

from __future__ import annotations

from typing import Optional, Literal
import numpy as np
from scipy import stats
from scipy.optimize import brentq


def effect_size_cohend(
    x: np.ndarray,
    y: np.ndarray,
    pooled: bool = True,
) -> float:
    """
    Cohen's d effect size.

    Parameters
    ----------
    x : ndarray
        First sample.
    y : ndarray
        Second sample.
    pooled : bool, default=True
        Use pooled standard deviation.

    Returns
    -------
    d : float
        Cohen's d effect size.

    Examples
    --------
    >>> from nalyst.stats import effect_size_cohend
    >>> d = effect_size_cohend(group1, group2)
    """
    x = np.asarray(x).flatten()
    y = np.asarray(y).flatten()

    n1, n2 = len(x), len(y)
    mean1, mean2 = np.mean(x), np.mean(y)
    var1, var2 = np.var(x, ddof=1), np.var(y, ddof=1)

    if pooled:
        pooled_std = np.sqrt(((n1 - 1) * var1 + (n2 - 1) * var2) / (n1 + n2 - 2))
        d = (mean1 - mean2) / pooled_std
    else:
        d = (mean1 - mean2) / np.sqrt((var1 + var2) / 2)

    return d


class TTestPower:
    """
    Power analysis for t-tests.

    Computes power, sample size, or effect size given the other parameters.

    Parameters
    ----------
    effect_size : float, optional
        Cohen's d effect size.
    nobs : int, optional
        Sample size per group.
    alpha : float, default=0.05
        Significance level.
    power : float, optional
        Statistical power.
    ratio : float, default=1.0
        Ratio of sample sizes (n2/n1).
    alternative : str, default='two-sided'
        Alternative hypothesis.

    Examples
    --------
    >>> from nalyst.stats import TTestPower
    >>> # Compute required sample size
    >>> power = TTestPower(effect_size=0.5, alpha=0.05, power=0.8)
    >>> n = power.solve_power(parameter='nobs')
    """

    def __init__(
        self,
        effect_size: Optional[float] = None,
        nobs: Optional[int] = None,
        alpha: float = 0.05,
        power: Optional[float] = None,
        ratio: float = 1.0,
        alternative: Literal['two-sided', 'larger', 'smaller'] = 'two-sided',
    ):
        self.effect_size = effect_size
        self.nobs = nobs
        self.alpha = alpha
        self.power = power
        self.ratio = ratio
        self.alternative = alternative

    def compute_power(
        self,
        effect_size: float,
        nobs: int,
        alpha: float = 0.05,
    ) -> float:
        """
        Compute statistical power.

        Parameters
        ----------
        effect_size : float
            Cohen's d.
        nobs : int
            Sample size per group.
        alpha : float
            Significance level.

        Returns
        -------
        power : float
        """
        # Non-centrality parameter
        n1 = nobs
        n2 = int(nobs * self.ratio)

        se = np.sqrt(1/n1 + 1/n2)
        ncp = abs(effect_size) / se

        df = n1 + n2 - 2

        if self.alternative == 'two-sided':
            t_crit = stats.t.ppf(1 - alpha/2, df)
            power = 1 - stats.nct.cdf(t_crit, df, ncp) + stats.nct.cdf(-t_crit, df, ncp)
        else:
            t_crit = stats.t.ppf(1 - alpha, df)
            power = 1 - stats.nct.cdf(t_crit, df, ncp)

        return power

    def solve_power(self, parameter: str = 'nobs') -> float:
        """
        Solve for missing parameter.

        Parameters
        ----------
        parameter : str
            Which parameter to solve for: 'nobs', 'effect_size', or 'power'.

        Returns
        -------
        value : float
            Solved parameter value.
        """
        if parameter == 'nobs':
            if self.effect_size is None or self.power is None:
                raise ValueError("Need effect_size and power to solve for nobs")

            # Binary search for sample size
            def power_diff(n):
                return self.compute_power(self.effect_size, int(n), self.alpha) - self.power

            # Find bounds
            low, high = 5, 10000
            while power_diff(high) < 0:
                high *= 2

            n = brentq(power_diff, low, high)
            return int(np.ceil(n))

        elif parameter == 'effect_size':
            if self.nobs is None or self.power is None:
                raise ValueError("Need nobs and power to solve for effect_size")

            def power_diff(d):
                return self.compute_power(d, self.nobs, self.alpha) - self.power

            d = brentq(power_diff, 0.01, 3.0)
            return d

        elif parameter == 'power':
            if self.effect_size is None or self.nobs is None:
                raise ValueError("Need effect_size and nobs to solve for power")

            return self.compute_power(self.effect_size, self.nobs, self.alpha)

        else:
            raise ValueError(f"Unknown parameter: {parameter}")


def sample_size_ttest(
    effect_size: float,
    alpha: float = 0.05,
    power: float = 0.8,
    ratio: float = 1.0,
    alternative: str = 'two-sided',
) -> int:
    """
    Compute sample size for t-test.

    Parameters
    ----------
    effect_size : float
        Cohen's d.
    alpha : float, default=0.05
        Significance level.
    power : float, default=0.8
        Desired power.
    ratio : float, default=1.0
        Sample size ratio (n2/n1).
    alternative : str, default='two-sided'
        Alternative hypothesis.

    Returns
    -------
    n : int
        Required sample size per group.

    Examples
    --------
    >>> from nalyst.stats import sample_size_ttest
    >>> n = sample_size_ttest(effect_size=0.5, power=0.8)
    """
    power_analysis = TTestPower(
        effect_size=effect_size,
        alpha=alpha,
        power=power,
        ratio=ratio,
        alternative=alternative,
    )
    return power_analysis.solve_power('nobs')


class FTestPower:
    """
    Power analysis for F-tests (ANOVA).

    Parameters
    ----------
    effect_size : float, optional
        Cohen's f effect size.
    k_groups : int, optional
        Number of groups.
    nobs : int, optional
        Total sample size.
    alpha : float, default=0.05
        Significance level.
    power : float, optional
        Statistical power.
    """

    def __init__(
        self,
        effect_size: Optional[float] = None,
        k_groups: Optional[int] = None,
        nobs: Optional[int] = None,
        alpha: float = 0.05,
        power: Optional[float] = None,
    ):
        self.effect_size = effect_size
        self.k_groups = k_groups
        self.nobs = nobs
        self.alpha = alpha
        self.power = power

    def compute_power(
        self,
        effect_size: float,
        k_groups: int,
        nobs: int,
        alpha: float = 0.05,
    ) -> float:
        """Compute power for ANOVA."""
        df1 = k_groups - 1
        df2 = nobs - k_groups

        # Non-centrality parameter
        ncp = nobs * effect_size**2

        f_crit = stats.f.ppf(1 - alpha, df1, df2)
        power = 1 - stats.ncf.cdf(f_crit, df1, df2, ncp)

        return power

    def solve_power(self, parameter: str = 'nobs') -> float:
        """Solve for missing parameter."""
        if parameter == 'nobs':
            if self.effect_size is None or self.power is None or self.k_groups is None:
                raise ValueError("Need effect_size, power, and k_groups")

            def power_diff(n):
                return self.compute_power(
                    self.effect_size, self.k_groups, int(n), self.alpha
                ) - self.power

            low, high = self.k_groups + 1, 10000
            n = brentq(power_diff, low, high)
            return int(np.ceil(n))

        elif parameter == 'power':
            if self.effect_size is None or self.nobs is None or self.k_groups is None:
                raise ValueError("Need effect_size, nobs, and k_groups")

            return self.compute_power(
                self.effect_size, self.k_groups, self.nobs, self.alpha
            )

        else:
            raise ValueError(f"Unknown parameter: {parameter}")


class ChiSquarePower:
    """
    Power analysis for chi-squared tests.

    Parameters
    ----------
    effect_size : float, optional
        Cohen's w effect size.
    nobs : int, optional
        Sample size.
    df : int, optional
        Degrees of freedom.
    alpha : float, default=0.05
        Significance level.
    power : float, optional
        Statistical power.
    """

    def __init__(
        self,
        effect_size: Optional[float] = None,
        nobs: Optional[int] = None,
        df: Optional[int] = None,
        alpha: float = 0.05,
        power: Optional[float] = None,
    ):
        self.effect_size = effect_size
        self.nobs = nobs
        self.df = df
        self.alpha = alpha
        self.power = power

    def compute_power(
        self,
        effect_size: float,
        nobs: int,
        df: int,
        alpha: float = 0.05,
    ) -> float:
        """Compute power for chi-squared test."""
        # Non-centrality parameter
        ncp = nobs * effect_size**2

        chi2_crit = stats.chi2.ppf(1 - alpha, df)
        power = 1 - stats.ncx2.cdf(chi2_crit, df, ncp)

        return power

    def solve_power(self, parameter: str = 'nobs') -> float:
        """Solve for missing parameter."""
        if parameter == 'nobs':
            if self.effect_size is None or self.power is None or self.df is None:
                raise ValueError("Need effect_size, power, and df")

            def power_diff(n):
                return self.compute_power(
                    self.effect_size, int(n), self.df, self.alpha
                ) - self.power

            low, high = 10, 100000
            n = brentq(power_diff, low, high)
            return int(np.ceil(n))

        elif parameter == 'power':
            if self.effect_size is None or self.nobs is None or self.df is None:
                raise ValueError("Need effect_size, nobs, and df")

            return self.compute_power(
                self.effect_size, self.nobs, self.df, self.alpha
            )

        else:
            raise ValueError(f"Unknown parameter: {parameter}")
