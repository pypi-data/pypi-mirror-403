"""
Stationarity tests for time series.
"""

from __future__ import annotations

from typing import Optional, Tuple, Dict, Any
import numpy as np
from scipy import stats
from scipy.linalg import solve


def adfuller(
    x: np.ndarray,
    maxlag: Optional[int] = None,
    regression: str = 'c',
    autolag: str = 'AIC',
) -> Tuple[float, float, int, int, Dict[str, float], float]:
    """
    Augmented Dickey-Fuller unit root test.

    The null hypothesis is that the series has a unit root (non-stationary).

    Parameters
    ----------
    x : ndarray
        Time series data.
    maxlag : int, optional
        Maximum lag to use. If None, uses 12*(nobs/100)^(1/4).
    regression : str, default='c'
        Constant and trend: 'c' (constant only), 'ct' (constant + trend),
        'ctt' (constant + trend + trend^2), 'n' (no constant/trend).
    autolag : str, default='AIC'
        Method to select lag: 'AIC', 'BIC', 't-stat', or None.

    Returns
    -------
    adf : float
        ADF test statistic.
    pvalue : float
        MacKinnon p-value.
    usedlag : int
        Number of lags used.
    nobs : int
        Number of observations used.
    critical_values : dict
        Critical values at 1%, 5%, 10%.
    icbest : float
        Best information criterion if autolag used.

    Examples
    --------
    >>> from nalyst.timeseries import adfuller
    >>> adf, pvalue, usedlag, nobs, crit, ic = adfuller(y)
    >>> if pvalue < 0.05:
    ...     print("Reject null: series is stationary")
    """
    x = np.asarray(x).flatten()
    n = len(x)

    if maxlag is None:
        maxlag = int(np.ceil(12 * (n / 100) ** 0.25))

    maxlag = min(maxlag, n // 2 - 1)

    # First difference
    dx = np.diff(x)

    # Best lag selection
    best_lag = 0
    best_ic = np.inf

    for lag in range(maxlag + 1):
        try:
            result = _adf_regression(x, dx, lag, regression)
            if autolag == 'AIC':
                ic = result['aic']
            elif autolag == 'BIC':
                ic = result['bic']
            else:
                ic = result['aic']

            if ic < best_ic:
                best_ic = ic
                best_lag = lag
        except Exception:
            continue

    # Run with best lag
    result = _adf_regression(x, dx, best_lag, regression)

    adf_stat = result['adf_stat']
    nobs_used = result['nobs']

    # MacKinnon p-value approximation
    pvalue = _mackinnon_pvalue(adf_stat, regression, nobs_used)

    # Critical values
    critical_values = _get_critical_values(regression, nobs_used)

    return adf_stat, pvalue, best_lag, nobs_used, critical_values, best_ic


def _adf_regression(
    x: np.ndarray,
    dx: np.ndarray,
    lag: int,
    regression: str
) -> Dict[str, float]:
    """Run ADF regression."""
    n = len(dx)

    # Dependent variable
    y = dx[lag:]

    # Lagged level
    x_lag = x[lag:-1]

    # Build design matrix
    X_list = [x_lag]

    # Add lagged differences
    for i in range(1, lag + 1):
        X_list.append(dx[lag-i:-i])

    # Add constant/trend
    nobs = len(y)
    if regression in ['c', 'ct', 'ctt']:
        X_list.append(np.ones(nobs))
    if regression in ['ct', 'ctt']:
        X_list.append(np.arange(1, nobs + 1))
    if regression == 'ctt':
        X_list.append(np.arange(1, nobs + 1) ** 2)

    X = np.column_stack(X_list)

    # OLS
    beta = np.linalg.lstsq(X, y, rcond=None)[0]
    resid = y - X @ beta

    # Standard error
    sigma2 = np.sum(resid ** 2) / (nobs - X.shape[1])
    XtX_inv = np.linalg.pinv(X.T @ X)
    se = np.sqrt(sigma2 * np.diag(XtX_inv))

    # ADF statistic (t-stat on lagged level coefficient)
    adf_stat = beta[0] / se[0]

    # Information criteria
    k = X.shape[1]
    log_likelihood = -nobs/2 * (np.log(2*np.pi) + np.log(sigma2) + 1)
    aic = -2 * log_likelihood + 2 * k
    bic = -2 * log_likelihood + k * np.log(nobs)

    return {
        'adf_stat': adf_stat,
        'nobs': nobs,
        'aic': aic,
        'bic': bic,
    }


def _mackinnon_pvalue(stat: float, regression: str, nobs: int) -> float:
    """Approximate MacKinnon p-value."""
    # Coefficients for different regressions
    if regression == 'c':
        tau = [-3.43035, -2.86154, -2.56677]
    elif regression == 'ct':
        tau = [-3.95877, -3.41049, -3.12705]
    elif regression == 'ctt':
        tau = [-4.37113, -3.83239, -3.55326]
    else:  # no constant
        tau = [-2.56574, -1.94100, -1.61682]

    # Simple p-value approximation
    if stat < tau[0]:
        return 0.01
    elif stat < tau[1]:
        return 0.01 + 0.04 * (stat - tau[0]) / (tau[1] - tau[0])
    elif stat < tau[2]:
        return 0.05 + 0.05 * (stat - tau[1]) / (tau[2] - tau[1])
    else:
        # Use normal approximation for large values
        return min(1.0, stats.norm.sf(-stat))


def _get_critical_values(regression: str, nobs: int) -> Dict[str, float]:
    """Get critical values."""
    if regression == 'c':
        return {'1%': -3.43, '5%': -2.86, '10%': -2.57}
    elif regression == 'ct':
        return {'1%': -3.96, '5%': -3.41, '10%': -3.13}
    elif regression == 'ctt':
        return {'1%': -4.37, '5%': -3.83, '10%': -3.55}
    else:
        return {'1%': -2.57, '5%': -1.94, '10%': -1.62}


def adf_test(x: np.ndarray, **kwargs) -> Dict[str, Any]:
    """
    Convenient wrapper for ADF test.

    Parameters
    ----------
    x : ndarray
        Time series data.
    **kwargs
        Additional arguments passed to adfuller.

    Returns
    -------
    result : dict
        Dictionary with test results.

    Examples
    --------
    >>> result = adf_test(y)
    >>> print(f"ADF Statistic: {result['statistic']:.4f}")
    >>> print(f"p-value: {result['p_value']:.4f}")
    >>> print(f"Stationary: {result['is_stationary']}")
    """
    adf, pvalue, usedlag, nobs, crit, ic = adfuller(x, **kwargs)

    return {
        'statistic': adf,
        'p_value': pvalue,
        'used_lag': usedlag,
        'n_obs': nobs,
        'critical_values': crit,
        'ic_best': ic,
        'is_stationary': pvalue < 0.05,
    }


def kpss(
    x: np.ndarray,
    regression: str = 'c',
    nlags: Optional[int] = None,
) -> Tuple[float, float, int, Dict[str, float]]:
    """
    KPSS test for stationarity.

    The null hypothesis is that the series is stationary.

    Parameters
    ----------
    x : ndarray
        Time series data.
    regression : str, default='c'
        'c' for level stationarity, 'ct' for trend stationarity.
    nlags : int, optional
        Number of lags for HAC estimator.

    Returns
    -------
    kpss_stat : float
        KPSS test statistic.
    pvalue : float
        Approximate p-value.
    nlags : int
        Number of lags used.
    critical_values : dict
        Critical values.

    Examples
    --------
    >>> kpss_stat, pvalue, lags, crit = kpss(y)
    >>> if pvalue > 0.05:
    ...     print("Fail to reject: series is stationary")
    """
    x = np.asarray(x).flatten()
    n = len(x)

    if nlags is None:
        nlags = int(np.ceil(4 * (n / 100) ** 0.25))

    # Residuals from regression
    if regression == 'ct':
        # Detrend
        t = np.arange(1, n + 1)
        X = np.column_stack([np.ones(n), t])
        beta = np.linalg.lstsq(X, x, rcond=None)[0]
        resid = x - X @ beta
    else:
        # Demean
        resid = x - np.mean(x)

    # Cumulative sum
    S = np.cumsum(resid)

    # Long-run variance (Newey-West)
    s2 = np.sum(resid ** 2) / n

    for lag in range(1, nlags + 1):
        weight = 1 - lag / (nlags + 1)
        gamma = np.sum(resid[lag:] * resid[:-lag]) / n
        s2 += 2 * weight * gamma

    # KPSS statistic
    kpss_stat = np.sum(S ** 2) / (n ** 2 * s2)

    # Critical values and p-value
    if regression == 'c':
        crit = {'10%': 0.347, '5%': 0.463, '2.5%': 0.574, '1%': 0.739}
    else:
        crit = {'10%': 0.119, '5%': 0.146, '2.5%': 0.176, '1%': 0.216}

    # Approximate p-value
    if regression == 'c':
        if kpss_stat > 0.739:
            pvalue = 0.01
        elif kpss_stat > 0.463:
            pvalue = 0.05
        elif kpss_stat > 0.347:
            pvalue = 0.10
        else:
            pvalue = 0.10 + 0.40 * (0.347 - kpss_stat) / 0.347
    else:
        if kpss_stat > 0.216:
            pvalue = 0.01
        elif kpss_stat > 0.146:
            pvalue = 0.05
        elif kpss_stat > 0.119:
            pvalue = 0.10
        else:
            pvalue = 0.10 + 0.40 * (0.119 - kpss_stat) / 0.119

    return kpss_stat, pvalue, nlags, crit


def kpss_test(x: np.ndarray, **kwargs) -> Dict[str, Any]:
    """
    Convenient wrapper for KPSS test.

    Parameters
    ----------
    x : ndarray
        Time series data.
    **kwargs
        Additional arguments passed to kpss.

    Returns
    -------
    result : dict
        Dictionary with test results.
    """
    stat, pvalue, nlags, crit = kpss(x, **kwargs)

    return {
        'statistic': stat,
        'p_value': pvalue,
        'n_lags': nlags,
        'critical_values': crit,
        'is_stationary': pvalue > 0.05,
    }
