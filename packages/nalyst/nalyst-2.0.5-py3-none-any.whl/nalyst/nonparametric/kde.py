"""
Kernel Density Estimation.
"""

from __future__ import annotations

from typing import Optional, Dict, Any, Union
import numpy as np


def silverman_bandwidth(data: np.ndarray) -> float:
    """
    Silverman's rule of thumb for bandwidth selection.

    h = 0.9 * min(std, IQR/1.34) * n^(-1/5)

    Parameters
    ----------
    data : ndarray
        Data samples.

    Returns
    -------
    h : float
        Bandwidth.
    """
    data = np.asarray(data).flatten()
    n = len(data)

    std = np.std(data)
    iqr = np.percentile(data, 75) - np.percentile(data, 25)

    A = min(std, iqr / 1.34) if iqr > 0 else std

    return 0.9 * A * n ** (-0.2)


def scott_bandwidth(data: np.ndarray) -> float:
    """
    Scott's rule for bandwidth selection.

    h = 1.06 * std * n^(-1/5)

    Parameters
    ----------
    data : ndarray
        Data samples.

    Returns
    -------
    h : float
        Bandwidth.
    """
    data = np.asarray(data).flatten()
    n = len(data)
    std = np.std(data)

    return 1.06 * std * n ** (-0.2)


class KernelDensity:
    """
    Kernel Density Estimation.

    Estimates probability density function using kernels.

    Parameters
    ----------
    kernel : str, default='gaussian'
        Kernel type: 'gaussian', 'epanechnikov', 'tophat', 'triangular'.
    bandwidth : float or str, default='silverman'
        Bandwidth value or selection method: 'silverman', 'scott'.

    Attributes
    ----------
    data_ : ndarray
        Fitted data.
    bandwidth_ : float
        Selected bandwidth.

    Examples
    --------
    >>> from nalyst.nonparametric import KernelDensity
    >>> kde = KernelDensity(kernel='gaussian')
    >>> kde.fit(data)
    >>> density = kde.evaluate(x_grid)
    """

    def __init__(
        self,
        kernel: str = 'gaussian',
        bandwidth: Union[float, str] = 'silverman',
    ):
        self.kernel = kernel
        self.bandwidth = bandwidth

    def fit(self, data: np.ndarray) -> "KernelDensity":
        """
        Fit the KDE.

        Parameters
        ----------
        data : ndarray of shape (n_samples,) or (n_samples, n_features)
            Data samples.

        Returns
        -------
        self
        """
        self.data_ = np.asarray(data)

        if self.data_.ndim == 1:
            self.data_ = self.data_.reshape(-1, 1)

        self.n_samples_, self.n_features_ = self.data_.shape

        # Select bandwidth
        if isinstance(self.bandwidth, str):
            if self.bandwidth == 'silverman':
                self.bandwidth_ = silverman_bandwidth(self.data_.flatten())
            elif self.bandwidth == 'scott':
                self.bandwidth_ = scott_bandwidth(self.data_.flatten())
            else:
                self.bandwidth_ = 1.0
        else:
            self.bandwidth_ = self.bandwidth

        return self

    def _kernel_fn(self, u: np.ndarray) -> np.ndarray:
        """Evaluate kernel function."""
        if self.kernel == 'gaussian':
            return np.exp(-0.5 * u ** 2) / np.sqrt(2 * np.pi)

        elif self.kernel == 'epanechnikov':
            return np.where(np.abs(u) <= 1, 0.75 * (1 - u ** 2), 0)

        elif self.kernel == 'tophat':
            return np.where(np.abs(u) <= 1, 0.5, 0)

        elif self.kernel == 'triangular':
            return np.where(np.abs(u) <= 1, 1 - np.abs(u), 0)

        else:  # Default to Gaussian
            return np.exp(-0.5 * u ** 2) / np.sqrt(2 * np.pi)

    def evaluate(self, x: np.ndarray) -> np.ndarray:
        """
        Evaluate density at points.

        Parameters
        ----------
        x : ndarray
            Points at which to evaluate density.

        Returns
        -------
        density : ndarray
            Density values.
        """
        x = np.asarray(x)

        if x.ndim == 1:
            x = x.reshape(-1, 1)

        n_eval = len(x)
        density = np.zeros(n_eval)

        for i in range(n_eval):
            # Distance to all data points
            if self.n_features_ == 1:
                u = (x[i, 0] - self.data_.flatten()) / self.bandwidth_
                density[i] = np.mean(self._kernel_fn(u)) / self.bandwidth_
            else:
                # Multivariate: product kernel
                kernel_vals = np.ones(self.n_samples_)
                for j in range(self.n_features_):
                    u = (x[i, j] - self.data_[:, j]) / self.bandwidth_
                    kernel_vals *= self._kernel_fn(u)

                density[i] = np.mean(kernel_vals) / (self.bandwidth_ ** self.n_features_)

        return density

    def score_samples(self, x: np.ndarray) -> np.ndarray:
        """
        Compute log-density at points.

        Parameters
        ----------
        x : ndarray
            Evaluation points.

        Returns
        -------
        log_density : ndarray
        """
        density = self.evaluate(x)
        return np.log(density + 1e-10)

    def sample(self, n_samples: int = 1, random_state: Optional[int] = None) -> np.ndarray:
        """
        Generate random samples from the fitted distribution.

        Parameters
        ----------
        n_samples : int
            Number of samples.
        random_state : int, optional
            Random seed.

        Returns
        -------
        samples : ndarray of shape (n_samples, n_features)
        """
        if random_state is not None:
            np.random.seed(random_state)

        # Sample from data points
        indices = np.random.choice(self.n_samples_, size=n_samples, replace=True)
        samples = self.data_[indices].copy()

        # Add kernel noise
        if self.kernel == 'gaussian':
            noise = np.random.normal(0, self.bandwidth_, size=samples.shape)
        else:
            # For other kernels, use uniform approximation
            noise = np.random.uniform(-self.bandwidth_, self.bandwidth_, size=samples.shape)

        samples += noise

        return samples


def gaussian_kde(
    data: np.ndarray,
    x: Optional[np.ndarray] = None,
    bandwidth: Optional[float] = None,
) -> Union[np.ndarray, "KernelDensity"]:
    """
    Gaussian kernel density estimation.

    Parameters
    ----------
    data : ndarray
        Data samples.
    x : ndarray, optional
        Points to evaluate. If None, returns fitted KDE.
    bandwidth : float, optional
        Bandwidth. If None, uses Silverman's rule.

    Returns
    -------
    density or kde : ndarray or KernelDensity
        Density values if x provided, else fitted KDE object.

    Examples
    --------
    >>> from nalyst.nonparametric import gaussian_kde
    >>> density = gaussian_kde(data, x_grid)
    """
    if bandwidth is None:
        bandwidth = 'silverman'

    kde = KernelDensity(kernel='gaussian', bandwidth=bandwidth)
    kde.fit(data)

    if x is None:
        return kde
    else:
        return kde.evaluate(x)
