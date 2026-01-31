"""
Autocorrelation functions and tests.
"""

from __future__ import annotations

from typing import Optional, Tuple, Dict, Any
import numpy as np
from scipy import stats


def acf(
    x: np.ndarray,
    nlags: int = 40,
    adjusted: bool = False,
    fft: bool = True,
    alpha: Optional[float] = None,
) -> np.ndarray:
    """
    Autocorrelation function.

    Parameters
    ----------
    x : ndarray
        Time series data.
    nlags : int, default=40
        Number of lags to compute.
    adjusted : bool, default=False
        If True, divide by n-k instead of n.
    fft : bool, default=True
        Use FFT for faster computation.
    alpha : float, optional
        If provided, compute confidence intervals.

    Returns
    -------
    acf_values : ndarray
        ACF values for lags 0 to nlags.
    confint : ndarray, optional
        Confidence intervals if alpha provided.

    Examples
    --------
    >>> from nalyst.timeseries import acf
    >>> acf_values = acf(y, nlags=20)
    """
    x = np.asarray(x).flatten()
    n = len(x)

    nlags = min(nlags, n - 1)

    # Demean
    x_demean = x - np.mean(x)

    if fft:
        # FFT-based computation
        nobs_pad = 2 ** int(np.ceil(np.log2(2 * n - 1)))
        fft_x = np.fft.fft(x_demean, n=nobs_pad)
        acov = np.fft.ifft(fft_x * np.conj(fft_x))[:n].real
    else:
        # Direct computation
        acov = np.zeros(n)
        for k in range(n):
            acov[k] = np.sum(x_demean[:n-k] * x_demean[k:])

    # Normalize
    if adjusted:
        divisor = np.array([n - k for k in range(nlags + 1)])
    else:
        divisor = n

    acf_values = acov[:nlags + 1] / acov[0]

    if alpha is not None:
        z = stats.norm.ppf(1 - alpha / 2)
        se = np.sqrt(1 / n)
        confint = np.column_stack([
            acf_values - z * se,
            acf_values + z * se
        ])
        return acf_values, confint

    return acf_values


def pacf(
    x: np.ndarray,
    nlags: int = 40,
    method: str = 'yw',
    alpha: Optional[float] = None,
) -> np.ndarray:
    """
    Partial autocorrelation function.

    Parameters
    ----------
    x : ndarray
        Time series data.
    nlags : int, default=40
        Number of lags.
    method : str, default='yw'
        Method: 'yw' (Yule-Walker), 'ols', 'burg'.
    alpha : float, optional
        If provided, compute confidence intervals.

    Returns
    -------
    pacf_values : ndarray
        PACF values.
    confint : ndarray, optional
        Confidence intervals if alpha provided.

    Examples
    --------
    >>> from nalyst.timeseries import pacf
    >>> pacf_values = pacf(y, nlags=20)
    """
    x = np.asarray(x).flatten()
    n = len(x)

    nlags = min(nlags, n // 2)

    if method == 'yw':
        pacf_values = _pacf_yw(x, nlags)
    elif method == 'ols':
        pacf_values = _pacf_ols(x, nlags)
    else:
        pacf_values = _pacf_yw(x, nlags)

    if alpha is not None:
        z = stats.norm.ppf(1 - alpha / 2)
        se = np.sqrt(1 / n)
        confint = np.column_stack([
            pacf_values - z * se,
            pacf_values + z * se
        ])
        return pacf_values, confint

    return pacf_values


def _pacf_yw(x: np.ndarray, nlags: int) -> np.ndarray:
    """PACF using Yule-Walker equations."""
    acf_values = acf(x, nlags=nlags)

    pacf_values = np.zeros(nlags + 1)
    pacf_values[0] = 1.0
    pacf_values[1] = acf_values[1]

    phi = np.zeros((nlags + 1, nlags + 1))
    phi[1, 1] = acf_values[1]

    for k in range(2, nlags + 1):
        # Compute phi_kk using Durbin-Levinson recursion
        num = acf_values[k] - np.sum(phi[k-1, 1:k] * acf_values[k-1:0:-1])
        denom = 1 - np.sum(phi[k-1, 1:k] * acf_values[1:k])

        if abs(denom) < 1e-10:
            pacf_values[k] = 0
        else:
            phi[k, k] = num / denom
            pacf_values[k] = phi[k, k]

        # Update other phi values
        for j in range(1, k):
            phi[k, j] = phi[k-1, j] - phi[k, k] * phi[k-1, k-j]

    return pacf_values


def _pacf_ols(x: np.ndarray, nlags: int) -> np.ndarray:
    """PACF using OLS regressions."""
    n = len(x)
    x = x - np.mean(x)

    pacf_values = np.zeros(nlags + 1)
    pacf_values[0] = 1.0

    for k in range(1, nlags + 1):
        # Regress x[t] on x[t-1], ..., x[t-k]
        y = x[k:]
        X = np.column_stack([x[k-i-1:n-i-1] for i in range(k)])

        if len(y) > X.shape[1]:
            beta = np.linalg.lstsq(X, y, rcond=None)[0]
            pacf_values[k] = beta[-1]
        else:
            pacf_values[k] = 0

    return pacf_values


def ccf(
    x: np.ndarray,
    y: np.ndarray,
    nlags: int = 40,
) -> np.ndarray:
    """
    Cross-correlation function.

    Parameters
    ----------
    x : ndarray
        First time series.
    y : ndarray
        Second time series.
    nlags : int, default=40
        Number of lags (both positive and negative).

    Returns
    -------
    ccf_values : ndarray
        CCF values from -nlags to +nlags.
    lags : ndarray
        Lag values.

    Examples
    --------
    >>> from nalyst.timeseries import ccf
    >>> ccf_values, lags = ccf(x, y, nlags=20)
    """
    x = np.asarray(x).flatten()
    y = np.asarray(y).flatten()

    n = min(len(x), len(y))
    x = x[:n]
    y = y[:n]

    nlags = min(nlags, n - 1)

    # Demean
    x = x - np.mean(x)
    y = y - np.mean(y)

    # Compute cross-correlation
    ccf_values = np.zeros(2 * nlags + 1)

    sx = np.std(x)
    sy = np.std(y)

    for k in range(-nlags, nlags + 1):
        if k >= 0:
            ccf_values[k + nlags] = np.sum(x[:n-k] * y[k:]) / (n * sx * sy)
        else:
            ccf_values[k + nlags] = np.sum(x[-k:] * y[:n+k]) / (n * sx * sy)

    lags = np.arange(-nlags, nlags + 1)

    return ccf_values, lags


def ljung_box(
    x: np.ndarray,
    lags: Optional[int] = None,
    model_df: int = 0,
    return_df: bool = True,
) -> Dict[str, np.ndarray]:
    """
    Ljung-Box test for autocorrelation.

    Tests the null hypothesis that there is no autocorrelation
    up to lag k.

    Parameters
    ----------
    x : ndarray
        Time series or residuals.
    lags : int, optional
        Number of lags to test. Default is min(10, n/5).
    model_df : int, default=0
        Degrees of freedom used by the model (e.g., p+q for ARMA).
    return_df : bool, default=True
        Return results as dictionary.

    Returns
    -------
    results : dict
        Dictionary with lb_stat, lb_pvalue for each lag.

    Examples
    --------
    >>> from nalyst.timeseries import ljung_box
    >>> result = ljung_box(residuals, lags=10)
    >>> print(result['lb_pvalue'])  # p-values for each lag
    """
    x = np.asarray(x).flatten()
    n = len(x)

    if lags is None:
        lags = min(10, n // 5)

    acf_values = acf(x, nlags=lags)[1:]  # Exclude lag 0

    lb_stat = np.zeros(lags)
    lb_pvalue = np.zeros(lags)

    # Cumulative Ljung-Box statistic
    for k in range(1, lags + 1):
        q_stat = n * (n + 2) * np.sum(acf_values[:k] ** 2 / (n - np.arange(1, k + 1)))
        lb_stat[k - 1] = q_stat

        df = max(1, k - model_df)
        lb_pvalue[k - 1] = 1 - stats.chi2.cdf(q_stat, df)

    return {
        'lb_stat': lb_stat,
        'lb_pvalue': lb_pvalue,
        'lags': np.arange(1, lags + 1),
    }
