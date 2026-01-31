"""
ARIMA and AutoARIMA models for time series forecasting.
"""

from __future__ import annotations

from typing import Optional, Tuple, List, Union
import warnings

import numpy as np
from scipy import optimize
from scipy.signal import lfilter

from nalyst.core.foundation import BaseLearner
from nalyst.core.validation import check_array


class ARIMA(BaseLearner):
    """
    AutoRegressive Integrated Moving Average model.

    ARIMA(p, d, q) where:
    - p: Order of the autoregressive part
    - d: Degree of differencing
    - q: Order of the moving average part

    Parameters
    ----------
    order : tuple of (p, d, q)
        The (p, d, q) order of the model.
    seasonal_order : tuple of (P, D, Q, s), optional
        The seasonal component (P, D, Q, s).
    trend : str, optional
        Include trend: 'n' (none), 'c' (constant), 't' (linear), 'ct' (both).

    Attributes
    ----------
    params_ : ndarray
        Fitted parameters.
    aic_ : float
        Akaike Information Criterion.
    bic_ : float
        Bayesian Information Criterion.
    resid_ : ndarray
        Residuals from the fit.

    Examples
    --------
    >>> from nalyst.timeseries import ARIMA
    >>> model = ARIMA(order=(1, 1, 1))
    >>> model.train(y)
    >>> forecast = model.forecast(steps=10)
    """

    def __init__(
        self,
        order: Tuple[int, int, int] = (1, 0, 0),
        seasonal_order: Optional[Tuple[int, int, int, int]] = None,
        trend: Optional[str] = None,
    ):
        self.order = order
        self.seasonal_order = seasonal_order
        self.trend = trend

    def train(self, y: np.ndarray, exog: Optional[np.ndarray] = None) -> "ARIMA":
        """
        Fit the ARIMA model.

        Parameters
        ----------
        y : ndarray of shape (n_samples,)
            Time series data.
        exog : ndarray, optional
            Exogenous variables.

        Returns
        -------
        self : ARIMA
            Fitted model.
        """
        y = np.asarray(y).flatten()
        self._y_orig = y.copy()
        self._n_obs = len(y)

        p, d, q = self.order

        # Apply differencing
        y_diff = self._difference(y, d)
        self._y_diff = y_diff

        # Estimate parameters using CSS (Conditional Sum of Squares)
        n_params = p + q + (1 if self.trend in ['c', 'ct'] else 0)

        if n_params == 0:
            self.params_ = np.array([])
            self.resid_ = y_diff
        else:
            # Initial parameter estimates
            x0 = np.zeros(n_params)

            # Optimize
            result = optimize.minimize(
                self._css_objective,
                x0,
                args=(y_diff, p, q),
                method='L-BFGS-B',
                options={'maxiter': 500}
            )

            self.params_ = result.x
            self.resid_ = self._compute_residuals(self.params_, y_diff, p, q)

        # Compute information criteria
        n = len(y_diff)
        k = len(self.params_) + 1  # +1 for variance
        sigma2 = np.var(self.resid_)

        log_likelihood = -n/2 * (np.log(2*np.pi) + np.log(sigma2) + 1)
        self.aic_ = -2 * log_likelihood + 2 * k
        self.bic_ = -2 * log_likelihood + k * np.log(n)

        # Store for forecasting
        self._sigma2 = sigma2
        self._fitted = True

        return self

    def _difference(self, y: np.ndarray, d: int) -> np.ndarray:
        """Apply differencing d times."""
        result = y.copy()
        for _ in range(d):
            result = np.diff(result)
        return result

    def _undifference(self, y_diff: np.ndarray, y_orig: np.ndarray, d: int) -> np.ndarray:
        """Reverse differencing."""
        result = y_diff.copy()
        for i in range(d):
            # Get the last value before this level of differencing
            last_val = y_orig[-(d - i)]
            result = np.cumsum(np.concatenate([[last_val], result]))
        return result[1:]

    def _css_objective(self, params: np.ndarray, y: np.ndarray, p: int, q: int) -> float:
        """Conditional sum of squares objective."""
        resid = self._compute_residuals(params, y, p, q)
        return np.sum(resid ** 2)

    def _compute_residuals(self, params: np.ndarray, y: np.ndarray, p: int, q: int) -> np.ndarray:
        """Compute residuals given parameters."""
        n = len(y)
        resid = np.zeros(n)

        # Extract AR and MA parameters
        if self.trend in ['c', 'ct']:
            const = params[0]
            ar_params = params[1:1+p] if p > 0 else np.array([])
            ma_params = params[1+p:1+p+q] if q > 0 else np.array([])
        else:
            const = 0
            ar_params = params[:p] if p > 0 else np.array([])
            ma_params = params[p:p+q] if q > 0 else np.array([])

        # Compute residuals recursively
        for t in range(n):
            pred = const

            # AR component
            for i, phi in enumerate(ar_params):
                if t - i - 1 >= 0:
                    pred += phi * y[t - i - 1]

            # MA component
            for j, theta in enumerate(ma_params):
                if t - j - 1 >= 0:
                    pred += theta * resid[t - j - 1]

            resid[t] = y[t] - pred

        return resid

    def forecast(self, steps: int = 1, exog: Optional[np.ndarray] = None) -> np.ndarray:
        """
        Generate forecasts.

        Parameters
        ----------
        steps : int
            Number of steps to forecast.
        exog : ndarray, optional
            Future exogenous variables.

        Returns
        -------
        forecast : ndarray of shape (steps,)
            Forecasted values.
        """
        self._check_is_trained()

        p, d, q = self.order

        # Get recent values and residuals
        y_ext = np.concatenate([self._y_diff, np.zeros(steps)])
        resid_ext = np.concatenate([self.resid_, np.zeros(steps)])

        # Extract parameters
        if self.trend in ['c', 'ct']:
            const = self.params_[0]
            ar_params = self.params_[1:1+p] if p > 0 else np.array([])
            ma_params = self.params_[1+p:1+p+q] if q > 0 else np.array([])
        else:
            const = 0
            ar_params = self.params_[:p] if p > 0 else np.array([])
            ma_params = self.params_[p:p+q] if q > 0 else np.array([])

        # Generate forecasts
        n = len(self._y_diff)
        forecasts_diff = np.zeros(steps)

        for h in range(steps):
            t = n + h
            pred = const

            # AR component
            for i, phi in enumerate(ar_params):
                if t - i - 1 >= n:
                    pred += phi * forecasts_diff[t - i - 1 - n]
                else:
                    pred += phi * self._y_diff[t - i - 1]

            # MA component (residuals are 0 for future)
            for j, theta in enumerate(ma_params):
                if t - j - 1 < n:
                    pred += theta * self.resid_[t - j - 1]

            forecasts_diff[h] = pred

        # Undifference if needed
        if d > 0:
            forecasts = self._undifference_forecast(forecasts_diff, d)
        else:
            forecasts = forecasts_diff

        return forecasts

    def _undifference_forecast(self, forecasts_diff: np.ndarray, d: int) -> np.ndarray:
        """Undifference forecasts."""
        result = forecasts_diff.copy()
        y = self._y_orig.copy()

        for _ in range(d):
            last_val = y[-1]
            result = last_val + np.cumsum(result)
            y = np.diff(y)

        return result

    def _check_is_trained(self):
        """Check if model is fitted."""
        if not hasattr(self, '_fitted') or not self._fitted:
            raise ValueError("Model must be trained before forecasting")

    def infer(self, steps: int = 1) -> np.ndarray:
        """Alias for forecast."""
        return self.forecast(steps=steps)

    def get_fitted_values(self) -> np.ndarray:
        """Get in-sample fitted values."""
        self._check_is_trained()
        return self._y_diff - self.resid_


class AutoARIMA(BaseLearner):
    """
    Automatic ARIMA model selection.

    Automatically selects the best ARIMA order using information criteria.

    Parameters
    ----------
    max_p : int, default=5
        Maximum AR order.
    max_d : int, default=2
        Maximum differencing order.
    max_q : int, default=5
        Maximum MA order.
    information_criterion : str, default='aic'
        Criterion for model selection: 'aic' or 'bic'.
    seasonal : bool, default=False
        Whether to consider seasonal models.
    m : int, default=1
        Seasonal period (if seasonal=True).
    stepwise : bool, default=True
        Use stepwise algorithm for faster search.

    Attributes
    ----------
    order_ : tuple
        Best (p, d, q) order.
    model_ : ARIMA
        Best fitted ARIMA model.

    Examples
    --------
    >>> from nalyst.timeseries import AutoARIMA
    >>> model = AutoARIMA(max_p=3, max_q=3)
    >>> model.train(y)
    >>> print(f"Best order: {model.order_}")
    >>> forecast = model.forecast(steps=10)
    """

    def __init__(
        self,
        max_p: int = 5,
        max_d: int = 2,
        max_q: int = 5,
        information_criterion: str = 'aic',
        seasonal: bool = False,
        m: int = 1,
        stepwise: bool = True,
    ):
        self.max_p = max_p
        self.max_d = max_d
        self.max_q = max_q
        self.information_criterion = information_criterion
        self.seasonal = seasonal
        self.m = m
        self.stepwise = stepwise

    def train(self, y: np.ndarray, exog: Optional[np.ndarray] = None) -> "AutoARIMA":
        """
        Find best ARIMA model and fit.

        Parameters
        ----------
        y : ndarray
            Time series data.
        exog : ndarray, optional
            Exogenous variables.

        Returns
        -------
        self : AutoARIMA
        """
        y = np.asarray(y).flatten()

        # Determine differencing order
        d = self._select_d(y)

        # Search for best (p, q)
        best_ic = np.inf
        best_order = (0, d, 0)
        best_model = None

        if self.stepwise:
            # Stepwise search
            orders_to_try = self._stepwise_search(y, d)
        else:
            # Grid search
            orders_to_try = [
                (p, d, q)
                for p in range(self.max_p + 1)
                for q in range(self.max_q + 1)
            ]

        for p, d_order, q in orders_to_try:
            try:
                model = ARIMA(order=(p, d_order, q))
                model.train(y)

                ic = model.aic_ if self.information_criterion == 'aic' else model.bic_

                if ic < best_ic:
                    best_ic = ic
                    best_order = (p, d_order, q)
                    best_model = model
            except Exception:
                continue

        if best_model is None:
            # Fallback to simple model
            best_model = ARIMA(order=(1, d, 0))
            best_model.train(y)
            best_order = (1, d, 0)

        self.order_ = best_order
        self.model_ = best_model
        self.aic_ = best_model.aic_
        self.bic_ = best_model.bic_

        return self

    def _select_d(self, y: np.ndarray) -> int:
        """Select differencing order using unit root tests."""
        from nalyst.timeseries.stationarity import adf_test

        for d in range(self.max_d + 1):
            y_diff = y.copy()
            for _ in range(d):
                y_diff = np.diff(y_diff)

            if len(y_diff) < 10:
                return d

            try:
                result = adf_test(y_diff)
                if result['p_value'] < 0.05:
                    return d
            except Exception:
                pass

        return self.max_d

    def _stepwise_search(self, y: np.ndarray, d: int) -> List[Tuple[int, int, int]]:
        """Generate orders for stepwise search."""
        # Start with simple models, expand as needed
        orders = [
            (0, d, 0), (1, d, 0), (0, d, 1), (1, d, 1),
            (2, d, 0), (0, d, 2), (2, d, 1), (1, d, 2), (2, d, 2),
        ]

        # Add higher orders
        for p in range(3, self.max_p + 1):
            orders.append((p, d, 0))
            orders.append((p, d, 1))

        for q in range(3, self.max_q + 1):
            orders.append((0, d, q))
            orders.append((1, d, q))

        return orders

    def forecast(self, steps: int = 1, exog: Optional[np.ndarray] = None) -> np.ndarray:
        """Generate forecasts using best model."""
        if not hasattr(self, 'model_'):
            raise ValueError("Model must be trained first")
        return self.model_.forecast(steps=steps, exog=exog)

    def infer(self, steps: int = 1) -> np.ndarray:
        """Alias for forecast."""
        return self.forecast(steps=steps)
