"""
Time series decomposition methods.
"""

from __future__ import annotations

from typing import Optional, Literal, NamedTuple
import numpy as np
from scipy.ndimage import uniform_filter1d


class DecompositionResult(NamedTuple):
    """Result of time series decomposition."""
    observed: np.ndarray
    trend: np.ndarray
    seasonal: np.ndarray
    resid: np.ndarray


def seasonal_decompose(
    x: np.ndarray,
    model: Literal['additive', 'multiplicative'] = 'additive',
    period: Optional[int] = None,
    filt: Optional[np.ndarray] = None,
    two_sided: bool = True,
    extrapolate_trend: int = 0,
) -> DecompositionResult:
    """
    Classical seasonal decomposition.

    Decomposes a time series into trend, seasonal, and residual components.

    Parameters
    ----------
    x : ndarray
        Time series data.
    model : {'additive', 'multiplicative'}, default='additive'
        Type of decomposition.
    period : int, optional
        Seasonal period. If None, will try to infer.
    filt : ndarray, optional
        Filter for trend estimation. Default is moving average.
    two_sided : bool, default=True
        Use two-sided moving average for trend.
    extrapolate_trend : int, default=0
        Number of points to extrapolate trend at edges.

    Returns
    -------
    result : DecompositionResult
        Named tuple with observed, trend, seasonal, resid.

    Examples
    --------
    >>> from nalyst.timeseries import seasonal_decompose
    >>> result = seasonal_decompose(y, period=12)
    >>> trend = result.trend
    >>> seasonal = result.seasonal
    >>> residual = result.resid
    """
    x = np.asarray(x).flatten()
    n = len(x)

    if period is None:
        period = _infer_period(x)

    if period < 2:
        raise ValueError("period must be >= 2")

    # Default filter: centered moving average
    if filt is None:
        if period % 2 == 0:
            # Even period: use period+1 weights with 0.5 at ends
            filt = np.ones(period + 1)
            filt[0] = filt[-1] = 0.5
            filt /= period
        else:
            filt = np.ones(period) / period

    # Compute trend using convolution
    trend = _convolve_trend(x, filt, two_sided)

    # Extrapolate trend if requested
    if extrapolate_trend > 0:
        trend = _extrapolate_trend(trend, extrapolate_trend)

    # Detrend
    if model == 'multiplicative':
        detrended = x / trend
    else:
        detrended = x - trend

    # Compute seasonal component
    seasonal = np.zeros(n)

    for i in range(period):
        indices = np.arange(i, n, period)
        valid = ~np.isnan(detrended[indices])
        if valid.any():
            seasonal[indices] = np.nanmean(detrended[indices])

    # Normalize seasonal (should sum to 0 for additive, period for multiplicative)
    if model == 'multiplicative':
        seasonal_mean = np.mean(seasonal[:period])
        seasonal /= seasonal_mean
    else:
        seasonal_mean = np.mean(seasonal[:period])
        seasonal -= seasonal_mean

    # Compute residual
    if model == 'multiplicative':
        resid = x / (trend * seasonal)
    else:
        resid = x - trend - seasonal

    return DecompositionResult(
        observed=x,
        trend=trend,
        seasonal=seasonal,
        resid=resid,
    )


def _convolve_trend(x: np.ndarray, filt: np.ndarray, two_sided: bool) -> np.ndarray:
    """Compute trend using filter convolution."""
    n = len(x)
    filt_len = len(filt)
    half = filt_len // 2

    trend = np.full(n, np.nan)

    if two_sided:
        for t in range(half, n - half):
            trend[t] = np.sum(filt * x[t - half:t + half + 1 if filt_len % 2 else t + half])
    else:
        for t in range(filt_len - 1, n):
            trend[t] = np.sum(filt * x[t - filt_len + 1:t + 1])

    return trend


def _extrapolate_trend(trend: np.ndarray, npoints: int) -> np.ndarray:
    """Extrapolate trend at edges."""
    result = trend.copy()

    # Find first and last valid points
    valid = ~np.isnan(trend)
    first_valid = np.argmax(valid)
    last_valid = len(trend) - 1 - np.argmax(valid[::-1])

    # Extrapolate at start
    if first_valid > 0:
        slope = (trend[first_valid + 1] - trend[first_valid]) if first_valid + 1 < len(trend) else 0
        for i in range(first_valid - 1, max(-1, first_valid - npoints - 1), -1):
            result[i] = trend[first_valid] + slope * (i - first_valid)

    # Extrapolate at end
    if last_valid < len(trend) - 1:
        slope = (trend[last_valid] - trend[last_valid - 1]) if last_valid > 0 else 0
        for i in range(last_valid + 1, min(len(trend), last_valid + npoints + 1)):
            result[i] = trend[last_valid] + slope * (i - last_valid)

    return result


def _infer_period(x: np.ndarray) -> int:
    """Try to infer seasonal period from ACF."""
    from nalyst.timeseries.autocorrelation import acf

    n = len(x)
    max_lag = min(n // 2, 100)

    acf_values = acf(x, nlags=max_lag)

    # Find first peak after lag 1
    for i in range(2, max_lag - 1):
        if acf_values[i] > acf_values[i-1] and acf_values[i] > acf_values[i+1]:
            if acf_values[i] > 0.1:  # Significant peak
                return i

    return 12  # Default


class STLDecomposition:
    """
    STL: Seasonal and Trend decomposition using Loess.

    Parameters
    ----------
    period : int
        Seasonal period.
    seasonal : int, default=7
        Length of seasonal smoother. Must be odd.
    trend : int, optional
        Length of trend smoother. Must be odd.
    low_pass : int, optional
        Length of low-pass filter.
    robust : bool, default=False
        Use robust fitting to downweight outliers.
    seasonal_deg : int, default=1
        Degree of seasonal LOESS (0 or 1).
    trend_deg : int, default=1
        Degree of trend LOESS (0 or 1).

    Attributes
    ----------
    trend_ : ndarray
        Trend component.
    seasonal_ : ndarray
        Seasonal component.
    resid_ : ndarray
        Residual component.

    Examples
    --------
    >>> from nalyst.timeseries import STLDecomposition
    >>> stl = STLDecomposition(period=12)
    >>> stl.fit(y)
    >>> trend = stl.trend_
    """

    def __init__(
        self,
        period: int,
        seasonal: int = 7,
        trend: Optional[int] = None,
        low_pass: Optional[int] = None,
        robust: bool = False,
        seasonal_deg: int = 1,
        trend_deg: int = 1,
    ):
        self.period = period
        self.seasonal = seasonal if seasonal % 2 == 1 else seasonal + 1
        self.trend = trend
        self.low_pass = low_pass
        self.robust = robust
        self.seasonal_deg = seasonal_deg
        self.trend_deg = trend_deg

    def fit(self, x: np.ndarray, n_iter: int = 2) -> "STLDecomposition":
        """
        Decompose the time series.

        Parameters
        ----------
        x : ndarray
            Time series data.
        n_iter : int, default=2
            Number of robustness iterations.

        Returns
        -------
        self : STLDecomposition
        """
        x = np.asarray(x).flatten()
        n = len(x)

        # Default parameters
        if self.trend is None:
            self.trend_ = int(np.ceil(1.5 * self.period / (1 - 1.5 / self.seasonal)))
            if self.trend_ % 2 == 0:
                self.trend_ += 1
        else:
            self.trend_ = self.trend

        if self.low_pass is None:
            self.low_pass_ = self.period + 1 if self.period % 2 == 0 else self.period
        else:
            self.low_pass_ = self.low_pass

        # Initialize
        seasonal = np.zeros(n)
        trend = np.zeros(n)
        weights = np.ones(n)

        n_outer = n_iter if self.robust else 1

        for _ in range(n_outer):
            for _ in range(2):  # Inner iterations
                # Step 1: Detrend
                detrended = x - trend

                # Step 2: Cycle subseries smoothing
                cycle_sub = np.zeros((self.period, (n - 1) // self.period + 1))

                for i in range(self.period):
                    indices = np.arange(i, n, self.period)
                    subseries = detrended[indices]
                    smoothed = self._loess_smooth(subseries, self.seasonal, weights[indices])
                    cycle_sub[i, :len(smoothed)] = smoothed

                # Step 3: Reconstruct seasonal
                seasonal_temp = np.zeros(n)
                for i in range(self.period):
                    indices = np.arange(i, n, self.period)
                    seasonal_temp[indices] = cycle_sub[i, :len(indices)]

                # Step 4: Low-pass filter
                low_pass = self._moving_average(seasonal_temp, self.period)
                low_pass = self._moving_average(low_pass, self.period)
                low_pass = self._loess_smooth(low_pass, self.low_pass_, weights)

                seasonal = seasonal_temp - low_pass

                # Step 5: Deseasonalize
                deseasonal = x - seasonal

                # Step 6: Trend smoothing
                trend = self._loess_smooth(deseasonal, self.trend_, weights)

            # Update weights for robust fitting
            if self.robust:
                resid = x - trend - seasonal
                h = 6 * np.median(np.abs(resid))
                weights = np.clip(1 - (np.abs(resid) / h) ** 2, 0, 1) ** 2

        self.seasonal_ = seasonal
        self.trend_ = trend
        self.resid_ = x - trend - seasonal
        self.observed_ = x

        return self

    def _loess_smooth(self, y: np.ndarray, span: int, weights: np.ndarray = None) -> np.ndarray:
        """Simple LOESS-like smoothing using weighted moving average."""
        n = len(y)
        if weights is None:
            weights = np.ones(n)

        half_span = span // 2
        smoothed = np.zeros(n)

        for i in range(n):
            start = max(0, i - half_span)
            end = min(n, i + half_span + 1)

            # Tricube weights
            distances = np.abs(np.arange(start, end) - i) / (half_span + 1)
            tricube = (1 - distances ** 3) ** 3

            w = tricube * weights[start:end]

            if np.sum(w) > 0:
                smoothed[i] = np.sum(w * y[start:end]) / np.sum(w)
            else:
                smoothed[i] = y[i]

        return smoothed

    def _moving_average(self, y: np.ndarray, window: int) -> np.ndarray:
        """Simple moving average."""
        n = len(y)
        result = np.zeros(n)
        half = window // 2

        for i in range(n):
            start = max(0, i - half)
            end = min(n, i + half + 1)
            result[i] = np.mean(y[start:end])

        return result
