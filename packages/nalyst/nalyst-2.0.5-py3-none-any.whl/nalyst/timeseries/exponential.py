"""
Exponential Smoothing models for time series forecasting.
"""

from __future__ import annotations

from typing import Optional, Literal
import numpy as np
from scipy import optimize

from nalyst.core.foundation import BaseLearner


class SimpleExponentialSmoothing(BaseLearner):
    """
    Simple Exponential Smoothing (SES).

    Suitable for series without trend or seasonality.

    Parameters
    ----------
    alpha : float, optional
        Smoothing parameter (0 < alpha < 1). If None, optimized automatically.

    Attributes
    ----------
    alpha_ : float
        Fitted smoothing parameter.
    level_ : ndarray
        Smoothed level values.
    sse_ : float
        Sum of squared errors.

    Examples
    --------
    >>> from nalyst.timeseries import SimpleExponentialSmoothing
    >>> model = SimpleExponentialSmoothing()
    >>> model.train(y)
    >>> forecast = model.forecast(steps=5)
    """

    def __init__(self, alpha: Optional[float] = None):
        self.alpha = alpha

    def train(self, y: np.ndarray) -> "SimpleExponentialSmoothing":
        """
        Fit the model.

        Parameters
        ----------
        y : ndarray
            Time series data.

        Returns
        -------
        self : SimpleExponentialSmoothing
        """
        y = np.asarray(y).flatten()
        self._y = y
        n = len(y)

        if self.alpha is not None:
            self.alpha_ = self.alpha
        else:
            # Optimize alpha
            result = optimize.minimize_scalar(
                lambda a: self._sse(a, y),
                bounds=(0.01, 0.99),
                method='bounded'
            )
            self.alpha_ = result.x

        # Compute smoothed values
        self.level_ = np.zeros(n)
        self.level_[0] = y[0]

        for t in range(1, n):
            self.level_[t] = self.alpha_ * y[t] + (1 - self.alpha_) * self.level_[t-1]

        # Compute SSE
        fitted = np.concatenate([[y[0]], self.level_[:-1]])
        self.sse_ = np.sum((y - fitted) ** 2)

        return self

    def _sse(self, alpha: float, y: np.ndarray) -> float:
        """Sum of squared errors for given alpha."""
        n = len(y)
        level = np.zeros(n)
        level[0] = y[0]

        for t in range(1, n):
            level[t] = alpha * y[t] + (1 - alpha) * level[t-1]

        fitted = np.concatenate([[y[0]], level[:-1]])
        return np.sum((y - fitted) ** 2)

    def forecast(self, steps: int = 1) -> np.ndarray:
        """
        Generate forecasts.

        Parameters
        ----------
        steps : int
            Number of steps to forecast.

        Returns
        -------
        forecast : ndarray
        """
        if not hasattr(self, 'level_'):
            raise ValueError("Model must be trained first")

        # SES forecasts are constant (last level)
        return np.full(steps, self.level_[-1])

    def infer(self, steps: int = 1) -> np.ndarray:
        """Alias for forecast."""
        return self.forecast(steps=steps)


class HoltLinear(BaseLearner):
    """
    Holt's Linear Trend method (Double Exponential Smoothing).

    Suitable for series with trend but no seasonality.

    Parameters
    ----------
    alpha : float, optional
        Level smoothing parameter.
    beta : float, optional
        Trend smoothing parameter.
    damped : bool, default=False
        Whether to use damped trend.
    phi : float, default=0.98
        Damping parameter (if damped=True).

    Attributes
    ----------
    alpha_ : float
        Fitted level smoothing parameter.
    beta_ : float
        Fitted trend smoothing parameter.
    level_ : ndarray
        Smoothed level values.
    trend_ : ndarray
        Smoothed trend values.

    Examples
    --------
    >>> from nalyst.timeseries import HoltLinear
    >>> model = HoltLinear()
    >>> model.train(y)
    >>> forecast = model.forecast(steps=10)
    """

    def __init__(
        self,
        alpha: Optional[float] = None,
        beta: Optional[float] = None,
        damped: bool = False,
        phi: float = 0.98,
    ):
        self.alpha = alpha
        self.beta = beta
        self.damped = damped
        self.phi = phi

    def train(self, y: np.ndarray) -> "HoltLinear":
        """Fit the model."""
        y = np.asarray(y).flatten()
        self._y = y
        n = len(y)

        # Optimize parameters if not provided
        if self.alpha is None or self.beta is None:
            result = optimize.minimize(
                lambda p: self._sse(p[0], p[1], y),
                x0=[0.3, 0.1],
                bounds=[(0.01, 0.99), (0.01, 0.99)],
                method='L-BFGS-B'
            )
            self.alpha_ = result.x[0]
            self.beta_ = result.x[1]
        else:
            self.alpha_ = self.alpha
            self.beta_ = self.beta

        # Initialize
        self.level_ = np.zeros(n)
        self.trend_ = np.zeros(n)

        self.level_[0] = y[0]
        self.trend_[0] = y[1] - y[0] if n > 1 else 0

        phi = self.phi if self.damped else 1.0

        # Smooth
        for t in range(1, n):
            self.level_[t] = self.alpha_ * y[t] + (1 - self.alpha_) * (self.level_[t-1] + phi * self.trend_[t-1])
            self.trend_[t] = self.beta_ * (self.level_[t] - self.level_[t-1]) + (1 - self.beta_) * phi * self.trend_[t-1]

        return self

    def _sse(self, alpha: float, beta: float, y: np.ndarray) -> float:
        """Sum of squared errors."""
        n = len(y)
        level = np.zeros(n)
        trend = np.zeros(n)

        level[0] = y[0]
        trend[0] = y[1] - y[0] if n > 1 else 0

        phi = self.phi if self.damped else 1.0

        for t in range(1, n):
            level[t] = alpha * y[t] + (1 - alpha) * (level[t-1] + phi * trend[t-1])
            trend[t] = beta * (level[t] - level[t-1]) + (1 - beta) * phi * trend[t-1]

        # One-step-ahead forecasts
        fitted = np.zeros(n)
        fitted[0] = y[0]
        for t in range(1, n):
            fitted[t] = level[t-1] + phi * trend[t-1]

        return np.sum((y - fitted) ** 2)

    def forecast(self, steps: int = 1) -> np.ndarray:
        """Generate forecasts."""
        if not hasattr(self, 'level_'):
            raise ValueError("Model must be trained first")

        phi = self.phi if self.damped else 1.0

        forecasts = np.zeros(steps)
        for h in range(1, steps + 1):
            if self.damped:
                phi_sum = np.sum([phi ** i for i in range(1, h + 1)])
                forecasts[h-1] = self.level_[-1] + phi_sum * self.trend_[-1]
            else:
                forecasts[h-1] = self.level_[-1] + h * self.trend_[-1]

        return forecasts

    def infer(self, steps: int = 1) -> np.ndarray:
        return self.forecast(steps=steps)


class HoltWinters(BaseLearner):
    """
    Holt-Winters Exponential Smoothing (Triple Exponential Smoothing).

    Suitable for series with trend and seasonality.

    Parameters
    ----------
    seasonal_periods : int
        Number of periods in a seasonal cycle.
    trend : str, default='add'
        Type of trend: 'add' (additive) or 'mul' (multiplicative).
    seasonal : str, default='add'
        Type of seasonality: 'add' (additive) or 'mul' (multiplicative).
    alpha : float, optional
        Level smoothing parameter.
    beta : float, optional
        Trend smoothing parameter.
    gamma : float, optional
        Seasonal smoothing parameter.
    damped : bool, default=False
        Whether to use damped trend.

    Attributes
    ----------
    alpha_ : float
        Fitted level smoothing parameter.
    beta_ : float
        Fitted trend smoothing parameter.
    gamma_ : float
        Fitted seasonal smoothing parameter.
    level_ : ndarray
        Smoothed level values.
    trend_ : ndarray
        Smoothed trend values.
    seasonal_ : ndarray
        Seasonal components.

    Examples
    --------
    >>> from nalyst.timeseries import HoltWinters
    >>> model = HoltWinters(seasonal_periods=12, seasonal='add')
    >>> model.train(y)
    >>> forecast = model.forecast(steps=12)
    """

    def __init__(
        self,
        seasonal_periods: int,
        trend: Literal['add', 'mul'] = 'add',
        seasonal: Literal['add', 'mul'] = 'add',
        alpha: Optional[float] = None,
        beta: Optional[float] = None,
        gamma: Optional[float] = None,
        damped: bool = False,
    ):
        self.seasonal_periods = seasonal_periods
        self.trend = trend
        self.seasonal = seasonal
        self.alpha = alpha
        self.beta = beta
        self.gamma = gamma
        self.damped = damped

    def train(self, y: np.ndarray) -> "HoltWinters":
        """Fit the model."""
        y = np.asarray(y).flatten()
        self._y = y
        n = len(y)
        m = self.seasonal_periods

        if n < 2 * m:
            raise ValueError(f"Need at least {2*m} observations for seasonal_periods={m}")

        # Initialize
        self.level_ = np.zeros(n)
        self.trend_ = np.zeros(n)
        self.seasonal_ = np.zeros(n + m)  # Extra space for forecasting

        # Initial values
        self.level_[0] = np.mean(y[:m])
        self.trend_[0] = (np.mean(y[m:2*m]) - np.mean(y[:m])) / m

        if self.seasonal == 'add':
            for i in range(m):
                self.seasonal_[i] = y[i] - self.level_[0]
        else:
            for i in range(m):
                self.seasonal_[i] = y[i] / self.level_[0]

        # Optimize if needed
        if self.alpha is None or self.beta is None or self.gamma is None:
            result = optimize.minimize(
                lambda p: self._sse(p[0], p[1], p[2], y),
                x0=[0.3, 0.1, 0.1],
                bounds=[(0.01, 0.99)] * 3,
                method='L-BFGS-B'
            )
            self.alpha_ = result.x[0]
            self.beta_ = result.x[1]
            self.gamma_ = result.x[2]
        else:
            self.alpha_ = self.alpha
            self.beta_ = self.beta
            self.gamma_ = self.gamma

        # Fit with optimal parameters
        self._smooth(y, self.alpha_, self.beta_, self.gamma_)

        return self

    def _smooth(self, y: np.ndarray, alpha: float, beta: float, gamma: float):
        """Apply smoothing with given parameters."""
        n = len(y)
        m = self.seasonal_periods

        for t in range(1, n):
            # Previous values
            l_prev = self.level_[t-1]
            b_prev = self.trend_[t-1]
            s_prev = self.seasonal_[t-m] if t >= m else self.seasonal_[t]

            if self.seasonal == 'add' and self.trend == 'add':
                self.level_[t] = alpha * (y[t] - s_prev) + (1 - alpha) * (l_prev + b_prev)
                self.trend_[t] = beta * (self.level_[t] - l_prev) + (1 - beta) * b_prev
                self.seasonal_[t] = gamma * (y[t] - self.level_[t]) + (1 - gamma) * s_prev
            elif self.seasonal == 'mul' and self.trend == 'add':
                self.level_[t] = alpha * (y[t] / s_prev) + (1 - alpha) * (l_prev + b_prev)
                self.trend_[t] = beta * (self.level_[t] - l_prev) + (1 - beta) * b_prev
                self.seasonal_[t] = gamma * (y[t] / self.level_[t]) + (1 - gamma) * s_prev
            elif self.seasonal == 'add' and self.trend == 'mul':
                self.level_[t] = alpha * (y[t] - s_prev) + (1 - alpha) * (l_prev * b_prev)
                self.trend_[t] = beta * (self.level_[t] / l_prev) + (1 - beta) * b_prev
                self.seasonal_[t] = gamma * (y[t] - self.level_[t]) + (1 - gamma) * s_prev
            else:  # mul, mul
                self.level_[t] = alpha * (y[t] / s_prev) + (1 - alpha) * (l_prev * b_prev)
                self.trend_[t] = beta * (self.level_[t] / l_prev) + (1 - beta) * b_prev
                self.seasonal_[t] = gamma * (y[t] / self.level_[t]) + (1 - gamma) * s_prev

    def _sse(self, alpha: float, beta: float, gamma: float, y: np.ndarray) -> float:
        """Compute SSE."""
        n = len(y)
        m = self.seasonal_periods

        level = np.zeros(n)
        trend = np.zeros(n)
        seasonal = np.zeros(n + m)

        level[0] = np.mean(y[:m])
        trend[0] = (np.mean(y[m:2*m]) - np.mean(y[:m])) / m

        if self.seasonal == 'add':
            for i in range(m):
                seasonal[i] = y[i] - level[0]
        else:
            for i in range(m):
                seasonal[i] = y[i] / level[0] if level[0] != 0 else 1

        sse = 0
        for t in range(1, n):
            l_prev = level[t-1]
            b_prev = trend[t-1]
            s_prev = seasonal[t-m] if t >= m else seasonal[t]

            # Forecast
            if self.seasonal == 'add' and self.trend == 'add':
                forecast = l_prev + b_prev + s_prev
                level[t] = alpha * (y[t] - s_prev) + (1 - alpha) * (l_prev + b_prev)
                trend[t] = beta * (level[t] - l_prev) + (1 - beta) * b_prev
                seasonal[t] = gamma * (y[t] - level[t]) + (1 - gamma) * s_prev
            elif self.seasonal == 'mul' and self.trend == 'add':
                forecast = (l_prev + b_prev) * s_prev
                level[t] = alpha * (y[t] / s_prev) + (1 - alpha) * (l_prev + b_prev)
                trend[t] = beta * (level[t] - l_prev) + (1 - beta) * b_prev
                seasonal[t] = gamma * (y[t] / level[t]) + (1 - gamma) * s_prev
            else:
                forecast = l_prev + b_prev + s_prev
                level[t] = alpha * (y[t] - s_prev) + (1 - alpha) * (l_prev + b_prev)
                trend[t] = beta * (level[t] - l_prev) + (1 - beta) * b_prev
                seasonal[t] = gamma * (y[t] - level[t]) + (1 - gamma) * s_prev

            sse += (y[t] - forecast) ** 2

        return sse

    def forecast(self, steps: int = 1) -> np.ndarray:
        """Generate forecasts."""
        if not hasattr(self, 'level_'):
            raise ValueError("Model must be trained first")

        m = self.seasonal_periods
        forecasts = np.zeros(steps)

        for h in range(1, steps + 1):
            s_idx = len(self._y) - m + ((h - 1) % m)
            s = self.seasonal_[s_idx]

            if self.seasonal == 'add' and self.trend == 'add':
                forecasts[h-1] = self.level_[-1] + h * self.trend_[-1] + s
            elif self.seasonal == 'mul' and self.trend == 'add':
                forecasts[h-1] = (self.level_[-1] + h * self.trend_[-1]) * s
            else:
                forecasts[h-1] = self.level_[-1] + h * self.trend_[-1] + s

        return forecasts

    def infer(self, steps: int = 1) -> np.ndarray:
        return self.forecast(steps=steps)
