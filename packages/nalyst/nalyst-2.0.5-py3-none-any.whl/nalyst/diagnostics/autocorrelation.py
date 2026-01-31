"""
Autocorrelation diagnostics.
"""

from __future__ import annotations

from typing import Tuple, Optional, Dict, Any
import numpy as np
from scipy import stats


def durbin_watson(resid: np.ndarray) -> float:
    """
    Durbin-Watson statistic for autocorrelation.

    Tests for first-order autocorrelation in residuals.

    Parameters
    ----------
    resid : ndarray
        Residuals from regression.

    Returns
    -------
    dw : float
        Durbin-Watson statistic (0 to 4).
        - dw  2: No autocorrelation
        - dw < 2: Positive autocorrelation
        - dw > 2: Negative autocorrelation

    Examples
    --------
    >>> from nalyst.diagnostics import durbin_watson
    >>> dw = durbin_watson(residuals)
    >>> if dw < 1.5 or dw > 2.5:
    ...     print("Possible autocorrelation")
    """
    resid = np.asarray(resid).flatten()
    n = len(resid)

    diff = np.diff(resid)
    dw = np.sum(diff ** 2) / np.sum(resid ** 2)

    return dw


def acorr_ljungbox(
    resid: np.ndarray,
    lags: Optional[int] = None,
    model_df: int = 0,
    return_df: bool = True,
) -> Dict[str, np.ndarray]:
    """
    Ljung-Box test for autocorrelation.

    Tests for significant autocorrelation at multiple lags.

    Parameters
    ----------
    resid : ndarray
        Residuals.
    lags : int, optional
        Maximum lag to test. Default is min(10, n/5).
    model_df : int, default=0
        Degrees of freedom used by the model.
    return_df : bool, default=True
        Return as dictionary.

    Returns
    -------
    result : dict
        lb_stat: Ljung-Box statistics for each lag.
        lb_pvalue: P-values for each lag.

    Examples
    --------
    >>> from nalyst.diagnostics import acorr_ljungbox
    >>> result = acorr_ljungbox(residuals, lags=10)
    >>> print(result['lb_pvalue'])
    """
    resid = np.asarray(resid).flatten()
    n = len(resid)

    if lags is None:
        lags = min(10, n // 5)

    # Compute autocorrelations
    resid_demean = resid - np.mean(resid)
    var = np.sum(resid_demean ** 2) / n

    acf_values = np.zeros(lags)
    for k in range(1, lags + 1):
        acf_values[k - 1] = np.sum(resid_demean[k:] * resid_demean[:-k]) / (n * var)

    # Ljung-Box statistic
    lb_stat = np.zeros(lags)
    lb_pvalue = np.zeros(lags)

    for k in range(1, lags + 1):
        q = n * (n + 2) * np.sum(acf_values[:k] ** 2 / (n - np.arange(1, k + 1)))
        lb_stat[k - 1] = q

        df = max(1, k - model_df)
        lb_pvalue[k - 1] = stats.chi2.sf(q, df)

    return {
        'lb_stat': lb_stat,
        'lb_pvalue': lb_pvalue,
        'lags': np.arange(1, lags + 1),
    }


def acorr_breusch_godfrey(
    resid: np.ndarray,
    exog: np.ndarray,
    nlags: int = 1,
) -> Tuple[float, float, float, float]:
    """
    Breusch-Godfrey Lagrange Multiplier test for autocorrelation.

    Parameters
    ----------
    resid : ndarray
        Residuals from regression.
    exog : ndarray
        Exogenous variables from original regression.
    nlags : int, default=1
        Number of lags to include.

    Returns
    -------
    lm : float
        Lagrange Multiplier statistic.
    lm_pvalue : float
        P-value for LM test.
    fvalue : float
        F-statistic.
    f_pvalue : float
        P-value for F-test.

    Examples
    --------
    >>> from nalyst.diagnostics import acorr_breusch_godfrey
    >>> lm, lm_p, f, f_p = acorr_breusch_godfrey(residuals, X, nlags=2)
    """
    resid = np.asarray(resid).flatten()
    exog = np.asarray(exog)

    n = len(resid)

    if exog.ndim == 1:
        exog = exog.reshape(-1, 1)

    # Add constant if not present
    if not np.allclose(exog[:, 0], 1):
        exog = np.column_stack([np.ones(n), exog])

    # Create lagged residuals
    lag_resid = np.zeros((n, nlags))
    for i in range(nlags):
        lag_resid[i+1:, i] = resid[:-i-1]

    # Auxiliary regression
    X_aux = np.column_stack([exog, lag_resid])

    # Regress residuals on original X and lagged residuals
    beta = np.linalg.lstsq(X_aux, resid, rcond=None)[0]
    fitted = X_aux @ beta

    # LM statistic
    ssr = np.sum((fitted - np.mean(resid)) ** 2)
    sst = np.sum((resid - np.mean(resid)) ** 2)

    r_squared = ssr / sst
    lm = n * r_squared
    lm_pvalue = stats.chi2.sf(lm, nlags)

    # F statistic
    sse = np.sum((resid - fitted) ** 2)
    k = X_aux.shape[1]
    fvalue = (ssr / nlags) / (sse / (n - k))
    f_pvalue = stats.f.sf(fvalue, nlags, n - k)

    return lm, lm_pvalue, fvalue, f_pvalue
