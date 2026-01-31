"""
Regression metrics.

Provides scoring functions for evaluating
regression models.
"""

from __future__ import annotations

from typing import Optional, Literal

import numpy as np


def mean_squared_error(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    *,
    sample_weight: Optional[np.ndarray] = None,
    multioutput: Literal["raw_values", "uniform_average"] = "uniform_average",
    squared: bool = True,
) -> float:
    """
    Compute mean squared error regression loss.

    Parameters
    ----------
    y_true : array-like of shape (n_samples,) or (n_samples, n_outputs)
        Ground truth target values.
    y_pred : array-like of shape (n_samples,) or (n_samples, n_outputs)
        Estimated target values.
    sample_weight : array-like of shape (n_samples,), optional
        Sample weights.
    multioutput : {"raw_values", "uniform_average"}, default="uniform_average"
        Defines aggregating of multiple output values.
    squared : bool, default=True
        If True returns MSE, if False returns RMSE.

    Returns
    -------
    loss : float or ndarray
        Mean squared error.

    Examples
    --------
    >>> from nalyst.metrics import mean_squared_error
    >>> y_true = [3, -0.5, 2, 7]
    >>> y_pred = [2.5, 0.0, 2, 8]
    >>> mean_squared_error(y_true, y_pred)
    0.375
    """
    y_true = np.asarray(y_true)
    y_pred = np.asarray(y_pred)

    errors = (y_true - y_pred) ** 2

    if sample_weight is not None:
        sample_weight = np.asarray(sample_weight)
        if errors.ndim == 1:
            mse = np.average(errors, weights=sample_weight)
        else:
            mse = np.average(errors, weights=sample_weight, axis=0)
    else:
        if errors.ndim == 1:
            mse = np.mean(errors)
        else:
            mse = np.mean(errors, axis=0)

    if not squared:
        mse = np.sqrt(mse)

    if multioutput == "uniform_average" and np.ndim(mse) > 0:
        mse = np.mean(mse)

    return float(mse) if np.ndim(mse) == 0 else mse


def root_mean_squared_error(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    *,
    sample_weight: Optional[np.ndarray] = None,
    multioutput: Literal["raw_values", "uniform_average"] = "uniform_average",
) -> float:
    """
    Compute root mean squared error regression loss.

    Parameters
    ----------
    y_true : array-like of shape (n_samples,) or (n_samples, n_outputs)
        Ground truth target values.
    y_pred : array-like of shape (n_samples,) or (n_samples, n_outputs)
        Estimated target values.
    sample_weight : array-like of shape (n_samples,), optional
        Sample weights.
    multioutput : {"raw_values", "uniform_average"}, default="uniform_average"
        Defines aggregating of multiple output values.

    Returns
    -------
    loss : float or ndarray
        Root mean squared error.

    Examples
    --------
    >>> from nalyst.metrics import root_mean_squared_error
    >>> y_true = [3, -0.5, 2, 7]
    >>> y_pred = [2.5, 0.0, 2, 8]
    >>> root_mean_squared_error(y_true, y_pred)
    0.612...
    """
    return mean_squared_error(
        y_true, y_pred,
        sample_weight=sample_weight,
        multioutput=multioutput,
        squared=False
    )


def mean_absolute_error(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    *,
    sample_weight: Optional[np.ndarray] = None,
    multioutput: Literal["raw_values", "uniform_average"] = "uniform_average",
) -> float:
    """
    Compute mean absolute error regression loss.

    Parameters
    ----------
    y_true : array-like of shape (n_samples,) or (n_samples, n_outputs)
        Ground truth target values.
    y_pred : array-like of shape (n_samples,) or (n_samples, n_outputs)
        Estimated target values.
    sample_weight : array-like of shape (n_samples,), optional
        Sample weights.
    multioutput : {"raw_values", "uniform_average"}, default="uniform_average"
        Defines aggregating of multiple output values.

    Returns
    -------
    loss : float or ndarray
        Mean absolute error.

    Examples
    --------
    >>> from nalyst.metrics import mean_absolute_error
    >>> y_true = [3, -0.5, 2, 7]
    >>> y_pred = [2.5, 0.0, 2, 8]
    >>> mean_absolute_error(y_true, y_pred)
    0.5
    """
    y_true = np.asarray(y_true)
    y_pred = np.asarray(y_pred)

    errors = np.abs(y_true - y_pred)

    if sample_weight is not None:
        sample_weight = np.asarray(sample_weight)
        if errors.ndim == 1:
            mae = np.average(errors, weights=sample_weight)
        else:
            mae = np.average(errors, weights=sample_weight, axis=0)
    else:
        if errors.ndim == 1:
            mae = np.mean(errors)
        else:
            mae = np.mean(errors, axis=0)

    if multioutput == "uniform_average" and np.ndim(mae) > 0:
        mae = np.mean(mae)

    return float(mae) if np.ndim(mae) == 0 else mae


def r2_score(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    *,
    sample_weight: Optional[np.ndarray] = None,
    multioutput: Literal["raw_values", "uniform_average", "variance_weighted"] = "uniform_average",
    force_finite: bool = True,
) -> float:
    """
    Compute R (coefficient of determination) score.

    Best possible score is 1.0. A constant model that predicts
    the mean of y would get a score of 0.0.

    Parameters
    ----------
    y_true : array-like of shape (n_samples,) or (n_samples, n_outputs)
        Ground truth target values.
    y_pred : array-like of shape (n_samples,) or (n_samples, n_outputs)
        Estimated target values.
    sample_weight : array-like of shape (n_samples,), optional
        Sample weights.
    multioutput : {"raw_values", "uniform_average", "variance_weighted"}, default="uniform_average"
        Defines aggregating of multiple output values.
    force_finite : bool, default=True
        Force finite output values (0.0 instead of nan/inf).

    Returns
    -------
    score : float or ndarray
        R score.

    Examples
    --------
    >>> from nalyst.metrics import r2_score
    >>> y_true = [3, -0.5, 2, 7]
    >>> y_pred = [2.5, 0.0, 2, 8]
    >>> r2_score(y_true, y_pred)
    0.948...
    """
    y_true = np.asarray(y_true)
    y_pred = np.asarray(y_pred)

    if sample_weight is not None:
        sample_weight = np.asarray(sample_weight)

    # Ensure 2D
    if y_true.ndim == 1:
        y_true = y_true.reshape(-1, 1)
        y_pred = y_pred.reshape(-1, 1)
        single_output = True
    else:
        single_output = False

    n_outputs = y_true.shape[1]
    scores = np.zeros(n_outputs)

    for i in range(n_outputs):
        y_t = y_true[:, i]
        y_p = y_pred[:, i]

        if sample_weight is not None:
            numerator = np.average((y_t - y_p) ** 2, weights=sample_weight)
            y_mean = np.average(y_t, weights=sample_weight)
            denominator = np.average((y_t - y_mean) ** 2, weights=sample_weight)
        else:
            numerator = np.mean((y_t - y_p) ** 2)
            denominator = np.mean((y_t - np.mean(y_t)) ** 2)

        if denominator == 0:
            if force_finite:
                scores[i] = 0.0 if numerator != 0 else 1.0
            else:
                scores[i] = float('nan')
        else:
            scores[i] = 1 - (numerator / denominator)

    if single_output:
        return float(scores[0])

    if multioutput == "raw_values":
        return scores
    elif multioutput == "uniform_average":
        return float(np.mean(scores))
    elif multioutput == "variance_weighted":
        # Weight by variance of each output
        variances = np.var(y_true, axis=0)
        if np.sum(variances) == 0:
            return float(np.mean(scores))
        return float(np.average(scores, weights=variances))

    return float(np.mean(scores))


def mean_absolute_percentage_error(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    *,
    sample_weight: Optional[np.ndarray] = None,
    multioutput: Literal["raw_values", "uniform_average"] = "uniform_average",
) -> float:
    """
    Compute mean absolute percentage error (MAPE).

    Parameters
    ----------
    y_true : array-like of shape (n_samples,) or (n_samples, n_outputs)
        Ground truth target values.
    y_pred : array-like of shape (n_samples,) or (n_samples, n_outputs)
        Estimated target values.
    sample_weight : array-like of shape (n_samples,), optional
        Sample weights.
    multioutput : {"raw_values", "uniform_average"}, default="uniform_average"
        Defines aggregating of multiple output values.

    Returns
    -------
    loss : float or ndarray
        Mean absolute percentage error as a decimal (not percentage).

    Examples
    --------
    >>> from nalyst.metrics import mean_absolute_percentage_error
    >>> y_true = [3, -0.5, 2, 7]
    >>> y_pred = [2.5, 0.0, 2, 8]
    >>> mean_absolute_percentage_error(y_true, y_pred)
    0.327...
    """
    y_true = np.asarray(y_true, dtype=np.float64)
    y_pred = np.asarray(y_pred, dtype=np.float64)

    # Avoid division by zero
    epsilon = np.finfo(np.float64).eps

    errors = np.abs((y_true - y_pred) / np.maximum(np.abs(y_true), epsilon))

    if sample_weight is not None:
        sample_weight = np.asarray(sample_weight)
        if errors.ndim == 1:
            mape = np.average(errors, weights=sample_weight)
        else:
            mape = np.average(errors, weights=sample_weight, axis=0)
    else:
        if errors.ndim == 1:
            mape = np.mean(errors)
        else:
            mape = np.mean(errors, axis=0)

    if multioutput == "uniform_average" and np.ndim(mape) > 0:
        mape = np.mean(mape)

    return float(mape) if np.ndim(mape) == 0 else mape


def explained_variance_score(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    *,
    sample_weight: Optional[np.ndarray] = None,
    multioutput: Literal["raw_values", "uniform_average", "variance_weighted"] = "uniform_average",
    force_finite: bool = True,
) -> float:
    """
    Compute explained variance score.

    Best possible score is 1.0, lower values are worse.

    Parameters
    ----------
    y_true : array-like of shape (n_samples,) or (n_samples, n_outputs)
        Ground truth target values.
    y_pred : array-like of shape (n_samples,) or (n_samples, n_outputs)
        Estimated target values.
    sample_weight : array-like of shape (n_samples,), optional
        Sample weights.
    multioutput : {"raw_values", "uniform_average", "variance_weighted"}, default="uniform_average"
        Defines aggregating of multiple output values.
    force_finite : bool, default=True
        Force finite output values.

    Returns
    -------
    score : float or ndarray
        Explained variance score.

    Examples
    --------
    >>> from nalyst.metrics import explained_variance_score
    >>> y_true = [3, -0.5, 2, 7]
    >>> y_pred = [2.5, 0.0, 2, 8]
    >>> explained_variance_score(y_true, y_pred)
    0.957...
    """
    y_true = np.asarray(y_true)
    y_pred = np.asarray(y_pred)

    if sample_weight is not None:
        sample_weight = np.asarray(sample_weight)

    # Ensure 2D
    if y_true.ndim == 1:
        y_true = y_true.reshape(-1, 1)
        y_pred = y_pred.reshape(-1, 1)
        single_output = True
    else:
        single_output = False

    n_outputs = y_true.shape[1]
    scores = np.zeros(n_outputs)

    for i in range(n_outputs):
        y_t = y_true[:, i]
        y_p = y_pred[:, i]
        diff = y_t - y_p

        if sample_weight is not None:
            diff_mean = np.average(diff, weights=sample_weight)
            numerator = np.average((diff - diff_mean) ** 2, weights=sample_weight)
            y_mean = np.average(y_t, weights=sample_weight)
            denominator = np.average((y_t - y_mean) ** 2, weights=sample_weight)
        else:
            numerator = np.var(diff)
            denominator = np.var(y_t)

        if denominator == 0:
            if force_finite:
                scores[i] = 0.0 if numerator != 0 else 1.0
            else:
                scores[i] = float('nan')
        else:
            scores[i] = 1 - (numerator / denominator)

    if single_output:
        return float(scores[0])

    if multioutput == "raw_values":
        return scores
    elif multioutput == "uniform_average":
        return float(np.mean(scores))
    elif multioutput == "variance_weighted":
        variances = np.var(y_true, axis=0)
        if np.sum(variances) == 0:
            return float(np.mean(scores))
        return float(np.average(scores, weights=variances))

    return float(np.mean(scores))


def max_error(
    y_true: np.ndarray,
    y_pred: np.ndarray,
) -> float:
    """
    Compute maximum residual error.

    Parameters
    ----------
    y_true : array-like of shape (n_samples,)
        Ground truth target values.
    y_pred : array-like of shape (n_samples,)
        Estimated target values.

    Returns
    -------
    max_error : float
        Maximum residual error.

    Examples
    --------
    >>> from nalyst.metrics import max_error
    >>> y_true = [3, 2, 7, 1]
    >>> y_pred = [4, 2, 7, 1]
    >>> max_error(y_true, y_pred)
    1
    """
    y_true = np.asarray(y_true)
    y_pred = np.asarray(y_pred)

    return float(np.max(np.abs(y_true - y_pred)))


def median_absolute_error(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    *,
    multioutput: Literal["raw_values", "uniform_average"] = "uniform_average",
) -> float:
    """
    Compute median absolute error regression loss.

    Parameters
    ----------
    y_true : array-like of shape (n_samples,) or (n_samples, n_outputs)
        Ground truth target values.
    y_pred : array-like of shape (n_samples,) or (n_samples, n_outputs)
        Estimated target values.
    multioutput : {"raw_values", "uniform_average"}, default="uniform_average"
        Defines aggregating of multiple output values.

    Returns
    -------
    loss : float or ndarray
        Median absolute error.

    Examples
    --------
    >>> from nalyst.metrics import median_absolute_error
    >>> y_true = [3, -0.5, 2, 7]
    >>> y_pred = [2.5, 0.0, 2, 8]
    >>> median_absolute_error(y_true, y_pred)
    0.5
    """
    y_true = np.asarray(y_true)
    y_pred = np.asarray(y_pred)

    errors = np.abs(y_true - y_pred)

    if errors.ndim == 1:
        return float(np.median(errors))

    medae = np.median(errors, axis=0)

    if multioutput == "uniform_average":
        return float(np.mean(medae))

    return medae


def mean_squared_log_error(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    *,
    sample_weight: Optional[np.ndarray] = None,
    multioutput: Literal["raw_values", "uniform_average"] = "uniform_average",
    squared: bool = True,
) -> float:
    """
    Compute mean squared logarithmic error regression loss.

    Parameters
    ----------
    y_true : array-like of shape (n_samples,) or (n_samples, n_outputs)
        Ground truth target values (must be positive).
    y_pred : array-like of shape (n_samples,) or (n_samples, n_outputs)
        Estimated target values (must be positive).
    sample_weight : array-like of shape (n_samples,), optional
        Sample weights.
    multioutput : {"raw_values", "uniform_average"}, default="uniform_average"
        Defines aggregating of multiple output values.
    squared : bool, default=True
        If True returns MSLE, if False returns RMSLE.

    Returns
    -------
    loss : float or ndarray
        Mean squared logarithmic error.

    Examples
    --------
    >>> from nalyst.metrics import mean_squared_log_error
    >>> y_true = [3, 5, 2.5, 7]
    >>> y_pred = [2.5, 5, 4, 8]
    >>> mean_squared_log_error(y_true, y_pred)
    0.039...
    """
    y_true = np.asarray(y_true)
    y_pred = np.asarray(y_pred)

    if np.any(y_true < 0) or np.any(y_pred < 0):
        raise ValueError("MSLE requires non-negative values")

    log_true = np.log1p(y_true)
    log_pred = np.log1p(y_pred)

    return mean_squared_error(
        log_true, log_pred,
        sample_weight=sample_weight,
        multioutput=multioutput,
        squared=squared
    )
