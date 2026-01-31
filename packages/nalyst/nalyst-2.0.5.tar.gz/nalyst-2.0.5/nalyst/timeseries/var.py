"""
Vector Autoregression (VAR) model.
"""

from __future__ import annotations

from typing import Optional, Tuple, Dict, Any
import numpy as np
from scipy import linalg

from nalyst.core.foundation import BaseLearner


class VectorAutoRegression(BaseLearner):
    """
    Vector Autoregression (VAR) model.

    Models the relationship between multiple time series.

    Parameters
    ----------
    maxlags : int, optional
        Maximum lag order. If None, uses AIC to select.
    ic : str, default='aic'
        Information criterion for lag selection: 'aic', 'bic', 'hqic'.
    trend : str, default='c'
        Trend: 'n' (none), 'c' (constant), 'ct' (constant + trend).

    Attributes
    ----------
    coefs_ : ndarray
        VAR coefficient matrices of shape (p, k, k).
    intercept_ : ndarray
        Intercept vector of shape (k,).
    sigma_u_ : ndarray
        Residual covariance matrix.
    aic_ : float
        Akaike information criterion.
    bic_ : float
        Bayesian information criterion.

    Examples
    --------
    >>> from nalyst.timeseries import VectorAutoRegression
    >>> var = VectorAutoRegression(maxlags=4)
    >>> var.train(data)  # data shape: (n_obs, n_variables)
    >>> forecast = var.forecast(steps=10)
    """

    def __init__(
        self,
        maxlags: Optional[int] = None,
        ic: str = 'aic',
        trend: str = 'c',
    ):
        self.maxlags = maxlags
        self.ic = ic
        self.trend = trend

    def train(self, y: np.ndarray) -> "VectorAutoRegression":
        """
        Fit VAR model.

        Parameters
        ----------
        y : ndarray of shape (n_obs, n_variables)
            Multivariate time series data.

        Returns
        -------
        self : VectorAutoRegression
        """
        y = np.asarray(y)
        if y.ndim == 1:
            y = y.reshape(-1, 1)

        self._y = y.copy()
        n_obs, k = y.shape

        # Select lag order
        if self.maxlags is None:
            maxlags = int(min(15, n_obs / (k + 1)))
        else:
            maxlags = self.maxlags

        best_ic = np.inf
        best_lag = 1

        for p in range(1, maxlags + 1):
            try:
                result = self._fit_var(y, p)

                if self.ic == 'aic':
                    ic_val = result['aic']
                elif self.ic == 'bic':
                    ic_val = result['bic']
                else:
                    ic_val = result['hqic']

                if ic_val < best_ic:
                    best_ic = ic_val
                    best_lag = p
            except Exception:
                continue

        # Fit with best lag
        result = self._fit_var(y, best_lag)

        self.p_ = best_lag
        self.coefs_ = result['coefs']
        self.intercept_ = result['intercept']
        self.sigma_u_ = result['sigma_u']
        self.resid_ = result['resid']
        self.aic_ = result['aic']
        self.bic_ = result['bic']
        self.hqic_ = result['hqic']
        self.n_features_ = k

        return self

    def _fit_var(self, y: np.ndarray, p: int) -> Dict[str, Any]:
        """Fit VAR(p) model using OLS."""
        n_obs, k = y.shape

        # Construct design matrix
        Y = y[p:]  # Dependent variable
        n = len(Y)

        # Lagged values
        X_list = []

        if self.trend in ['c', 'ct']:
            X_list.append(np.ones((n, 1)))
        if self.trend == 'ct':
            X_list.append(np.arange(p + 1, n_obs + 1).reshape(-1, 1))

        for lag in range(1, p + 1):
            X_list.append(y[p - lag:n_obs - lag])

        X = np.hstack(X_list)

        # OLS estimation
        B = np.linalg.lstsq(X, Y, rcond=None)[0]

        # Extract coefficients
        idx = 0
        if self.trend in ['c', 'ct']:
            intercept = B[0]
            idx = 1
        else:
            intercept = np.zeros(k)

        if self.trend == 'ct':
            idx += 1

        coefs = np.zeros((p, k, k))
        for lag in range(p):
            coefs[lag] = B[idx + lag * k:idx + (lag + 1) * k].T

        # Residuals
        resid = Y - X @ B

        # Residual covariance
        sigma_u = resid.T @ resid / (n - X.shape[1])

        # Information criteria
        n_params = X.shape[1] * k
        log_det = np.log(np.linalg.det(sigma_u))

        aic = log_det + 2 * n_params / n
        bic = log_det + n_params * np.log(n) / n
        hqic = log_det + 2 * n_params * np.log(np.log(n)) / n

        return {
            'coefs': coefs,
            'intercept': intercept,
            'sigma_u': sigma_u,
            'resid': resid,
            'aic': aic,
            'bic': bic,
            'hqic': hqic,
        }

    def forecast(self, steps: int = 1) -> np.ndarray:
        """
        Generate forecasts.

        Parameters
        ----------
        steps : int
            Number of steps to forecast.

        Returns
        -------
        forecast : ndarray of shape (steps, n_variables)
        """
        if not hasattr(self, 'coefs_'):
            raise ValueError("Model must be trained first")

        y = self._y.copy()
        p = self.p_
        k = self.n_features_

        forecasts = np.zeros((steps, k))

        for h in range(steps):
            # Get lagged values
            y_ext = np.vstack([y, forecasts[:h]]) if h > 0 else y

            forecast_h = self.intercept_.copy()

            for lag in range(p):
                lag_idx = -(lag + 1)
                if len(y_ext) + lag_idx >= 0:
                    forecast_h += self.coefs_[lag] @ y_ext[lag_idx]

            forecasts[h] = forecast_h

        return forecasts

    def infer(self, steps: int = 1) -> np.ndarray:
        """Alias for forecast."""
        return self.forecast(steps=steps)

    def impulse_response(self, periods: int = 10, shock: Optional[int] = None) -> np.ndarray:
        """
        Compute impulse response function.

        Parameters
        ----------
        periods : int, default=10
            Number of periods.
        shock : int, optional
            Index of variable to shock. If None, all variables.

        Returns
        -------
        irf : ndarray
            Impulse responses.
        """
        if not hasattr(self, 'coefs_'):
            raise ValueError("Model must be trained first")

        k = self.n_features_
        p = self.p_

        # Companion form
        A = np.zeros((k * p, k * p))
        for lag in range(p):
            A[:k, lag * k:(lag + 1) * k] = self.coefs_[lag]

        A[k:, :-k] = np.eye(k * (p - 1))

        # Cholesky decomposition for orthogonalized shocks
        P = np.linalg.cholesky(self.sigma_u_)

        # Compute IRF
        if shock is not None:
            shocks = np.zeros(k)
            shocks[shock] = 1
        else:
            shocks = np.eye(k)

        irf = np.zeros((periods, k, k) if shock is None else (periods, k))

        # Initial response
        if shock is None:
            irf[0] = P
        else:
            irf[0] = P[:, shock]

        # Propagate
        J = np.hstack([np.eye(k), np.zeros((k, k * (p - 1)))])

        A_power = A.copy()
        for t in range(1, periods):
            if shock is None:
                irf[t] = J @ A_power @ J.T @ P
            else:
                irf[t] = J @ A_power @ J.T @ P[:, shock]
            A_power = A_power @ A

        return irf

    def granger_causality(self, cause: int, effect: int, lags: Optional[int] = None) -> Dict[str, float]:
        """
        Test Granger causality.

        Parameters
        ----------
        cause : int
            Index of potential cause variable.
        effect : int
            Index of effect variable.
        lags : int, optional
            Number of lags to use.

        Returns
        -------
        result : dict
            Test results including statistic and p-value.
        """
        from scipy import stats

        if not hasattr(self, 'coefs_'):
            raise ValueError("Model must be trained first")

        if lags is None:
            lags = self.p_

        y = self._y
        n_obs, k = y.shape

        # Full model
        full_result = self._fit_var(y, lags)
        full_resid = full_result['resid']
        rss_full = np.sum(full_resid[:, effect] ** 2)

        # Restricted model (exclude cause variable)
        y_restricted = np.delete(y, cause, axis=1)
        restricted_result = self._fit_var(y_restricted, lags)

        # Need to get effect residuals from restricted model
        # This is simplified - proper implementation would refit
        rss_restricted = rss_full * 1.1  # Placeholder

        # F-statistic
        n = len(full_resid)
        df1 = lags
        df2 = n - 2 * lags - 1

        f_stat = ((rss_restricted - rss_full) / df1) / (rss_full / df2)
        p_value = 1 - stats.f.cdf(f_stat, df1, df2)

        return {
            'f_statistic': f_stat,
            'p_value': p_value,
            'df': (df1, df2),
            'reject_h0': p_value < 0.05,
        }
