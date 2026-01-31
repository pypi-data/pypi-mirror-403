"""
Residual analysis and diagnostics.
"""

from __future__ import annotations

from typing import Tuple, Optional, Dict, Any
import numpy as np
from scipy import stats


def residual_plots(
    y: np.ndarray,
    y_pred: np.ndarray,
    X: Optional[np.ndarray] = None,
) -> Dict[str, np.ndarray]:
    """
    Compute data for standard residual diagnostic plots.

    Parameters
    ----------
    y : ndarray
        Observed values.
    y_pred : ndarray
        Predicted values.
    X : ndarray, optional
        Design matrix for leverage computation.

    Returns
    -------
    result : dict
        Various residual measures and plot data.

    Examples
    --------
    >>> from nalyst.diagnostics import residual_plots
    >>> data = residual_plots(y, y_pred, X)
    """
    y = np.asarray(y).flatten()
    y_pred = np.asarray(y_pred).flatten()

    n = len(y)

    # Raw residuals
    residuals = y - y_pred

    # Standardized residuals
    sigma = np.std(residuals, ddof=1)
    std_residuals = residuals / sigma

    # For leverage and Cook's distance, we need X
    if X is not None:
        X = np.asarray(X)
        if X.ndim == 1:
            X = X.reshape(-1, 1)

        if not np.allclose(X[:, 0], 1):
            X = np.column_stack([np.ones(n), X])

        k = X.shape[1]

        # Hat matrix diagonal (leverage)
        try:
            XtX_inv = np.linalg.inv(X.T @ X)
            leverage = np.diag(X @ XtX_inv @ X.T)
        except np.linalg.LinAlgError:
            leverage = np.zeros(n)

        # Studentized residuals
        student_residuals = residuals / (sigma * np.sqrt(1 - leverage + 1e-10))

        # Cook's distance
        cooks_d = (student_residuals ** 2 * leverage) / (k * (1 - leverage + 1e-10))

        # DFFITS
        dffits = student_residuals * np.sqrt(leverage / (1 - leverage + 1e-10))
    else:
        leverage = np.zeros(n)
        student_residuals = std_residuals
        cooks_d = np.zeros(n)
        dffits = np.zeros(n)
        k = 1

    return {
        'residuals': residuals,
        'standardized_residuals': std_residuals,
        'studentized_residuals': student_residuals,
        'leverage': leverage,
        'cooks_distance': cooks_d,
        'dffits': dffits,
        'fitted_values': y_pred,
        'observed': y,
    }


def qq_plot_data(residuals: np.ndarray) -> Dict[str, np.ndarray]:
    """
    Compute data for Q-Q plot.

    Parameters
    ----------
    residuals : ndarray
        Residuals to check for normality.

    Returns
    -------
    result : dict
        theoretical: Theoretical quantiles.
        sample: Sample quantiles (sorted residuals).
        line_x, line_y: Reference line coordinates.

    Examples
    --------
    >>> from nalyst.diagnostics import qq_plot_data
    >>> data = qq_plot_data(residuals)
    >>> # Plot data['sample'] vs data['theoretical']
    """
    residuals = np.asarray(residuals).flatten()
    n = len(residuals)

    # Sort residuals
    sorted_resid = np.sort(residuals)

    # Standardize
    mean = np.mean(residuals)
    std = np.std(residuals, ddof=1)
    sorted_std = (sorted_resid - mean) / std

    # Theoretical quantiles
    prob = (np.arange(1, n + 1) - 0.5) / n
    theoretical = stats.norm.ppf(prob)

    # Reference line (robust fit)
    q1_idx = int(0.25 * n)
    q3_idx = int(0.75 * n)

    x1, x2 = theoretical[q1_idx], theoretical[q3_idx]
    y1, y2 = sorted_std[q1_idx], sorted_std[q3_idx]

    slope = (y2 - y1) / (x2 - x1)
    intercept = y1 - slope * x1

    line_x = np.array([theoretical[0], theoretical[-1]])
    line_y = intercept + slope * line_x

    return {
        'theoretical': theoretical,
        'sample': sorted_std,
        'line_x': line_x,
        'line_y': line_y,
    }


def influence_measures(
    y: np.ndarray,
    X: np.ndarray,
) -> Dict[str, np.ndarray]:
    """
    Compute influence diagnostics for each observation.

    Parameters
    ----------
    y : ndarray
        Dependent variable.
    X : ndarray
        Design matrix.

    Returns
    -------
    result : dict
        leverage: Hat matrix diagonal.
        cooks_d: Cook's distance.
        dffits: DFFITS values.
        dfbetas: DFBETAS for each coefficient.
        student_resid: Externally studentized residuals.

    Examples
    --------
    >>> from nalyst.diagnostics import influence_measures
    >>> result = influence_measures(y, X)
    >>> high_influence = result['cooks_distance'] > 4/len(y)
    """
    y = np.asarray(y).flatten()
    X = np.asarray(X)

    n = len(y)

    if X.ndim == 1:
        X = X.reshape(-1, 1)

    if not np.allclose(X[:, 0], 1):
        X = np.column_stack([np.ones(n), X])

    k = X.shape[1]

    # Fit model
    beta = np.linalg.lstsq(X, y, rcond=None)[0]
    fitted = X @ beta
    residuals = y - fitted

    # MSE
    mse = np.sum(residuals ** 2) / (n - k)

    # Hat matrix
    try:
        XtX_inv = np.linalg.inv(X.T @ X)
    except np.linalg.LinAlgError:
        XtX_inv = np.linalg.pinv(X.T @ X)

    H = X @ XtX_inv @ X.T
    leverage = np.diag(H)

    # Leave-one-out residuals
    resid_loo = residuals / (1 - leverage)

    # Leave-one-out MSE
    mse_loo = (np.sum(residuals ** 2) - residuals ** 2 / (1 - leverage)) / (n - k - 1)
    mse_loo = np.maximum(mse_loo, 1e-10)

    # Studentized residuals (external)
    student_resid = residuals / np.sqrt(mse_loo * (1 - leverage))

    # Cook's distance
    cooks_d = (residuals ** 2 / (k * mse)) * (leverage / (1 - leverage) ** 2)

    # DFFITS
    dffits = student_resid * np.sqrt(leverage / (1 - leverage))

    # DFBETAS
    dfbetas = np.zeros((n, k))
    for i in range(n):
        dfbetas[i] = (XtX_inv @ X[i] * resid_loo[i]) / np.sqrt(np.diag(XtX_inv) * mse_loo[i])

    return {
        'leverage': leverage,
        'cooks_distance': cooks_d,
        'dffits': dffits,
        'dfbetas': dfbetas,
        'studentized_residuals': student_resid,
        'residuals': residuals,
    }


def outlier_test(
    y: np.ndarray,
    X: np.ndarray,
    alpha: float = 0.05,
    method: str = 'bonferroni',
) -> Dict[str, Any]:
    """
    Test for outliers using studentized residuals.

    Parameters
    ----------
    y : ndarray
        Dependent variable.
    X : ndarray
        Design matrix.
    alpha : float, default=0.05
        Significance level.
    method : str, default='bonferroni'
        Multiple testing correction: 'bonferroni' or 'none'.

    Returns
    -------
    result : dict
        outliers: Indices of detected outliers.
        studentized_residuals: All studentized residuals.
        critical_value: Critical value used.
        p_values: P-values for each observation.

    Examples
    --------
    >>> from nalyst.diagnostics import outlier_test
    >>> result = outlier_test(y, X)
    >>> print(f"Outliers at indices: {result['outliers']}")
    """
    infl = influence_measures(y, X)
    student_resid = infl['studentized_residuals']

    n = len(y)
    k = X.shape[1] if X.ndim > 1 else 1

    # Degrees of freedom
    df = n - k - 1

    # P-values (two-tailed)
    p_values = 2 * stats.t.sf(np.abs(student_resid), df)

    # Critical value
    if method == 'bonferroni':
        alpha_adj = alpha / n
    else:
        alpha_adj = alpha

    critical_value = stats.t.ppf(1 - alpha_adj / 2, df)

    # Identify outliers
    outliers = np.where(np.abs(student_resid) > critical_value)[0]

    return {
        'outliers': outliers,
        'studentized_residuals': student_resid,
        'critical_value': critical_value,
        'p_values': p_values,
        'method': method,
    }
