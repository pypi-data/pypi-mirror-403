"""
Kernel functions for Gaussian Processes.
"""

from __future__ import annotations

from typing import Optional, Tuple
from abc import ABC, abstractmethod

import numpy as np
from scipy.spatial.distance import cdist, pdist, squareform


class Kernel(ABC):
    """Base class for kernels."""

    @abstractmethod
    def __call__(self, X: np.ndarray, Y: np.ndarray = None) -> np.ndarray:
        """Evaluate the kernel."""
        pass

    def diag(self, X: np.ndarray) -> np.ndarray:
        """Return diagonal of the kernel matrix."""
        return np.diag(self(X))

    def __add__(self, other: "Kernel") -> "Sum":
        return Sum(self, other)

    def __mul__(self, other: "Kernel") -> "Product":
        return Product(self, other)

    def __radd__(self, other):
        if other == 0:
            return self
        return Sum(other, self)

    def __rmul__(self, other):
        if other == 1:
            return self
        return Product(other, self)


class RBF(Kernel):
    """
    Radial Basis Function (Squared Exponential) kernel.

    k(x, y) = exp(-||x - y||^2 / (2 * length_scale^2))

    Parameters
    ----------
    length_scale : float, default=1.0
        The length scale of the kernel.
    length_scale_bounds : tuple, default=(1e-5, 1e5)
        Bounds for length scale during optimization.

    Examples
    --------
    >>> from nalyst.gaussian_process import RBF
    >>> kernel = RBF(length_scale=1.0)
    >>> X = np.array([[1, 2], [3, 4]])
    >>> K = kernel(X)
    """

    def __init__(
        self,
        length_scale: float = 1.0,
        length_scale_bounds: Tuple[float, float] = (1e-5, 1e5),
    ):
        self.length_scale = length_scale
        self.length_scale_bounds = length_scale_bounds

    def __call__(self, X: np.ndarray, Y: np.ndarray = None) -> np.ndarray:
        if Y is None:
            dists = squareform(pdist(X, metric='sqeuclidean'))
        else:
            dists = cdist(X, Y, metric='sqeuclidean')

        return np.exp(-dists / (2 * self.length_scale ** 2))

    def diag(self, X: np.ndarray) -> np.ndarray:
        return np.ones(X.shape[0])

    def __repr__(self) -> str:
        return f"RBF(length_scale={self.length_scale})"


class Matern(Kernel):
    """
    Matern kernel.

    Parameters
    ----------
    length_scale : float, default=1.0
        The length scale of the kernel.
    nu : float, default=1.5
        The smoothness parameter.
    length_scale_bounds : tuple, default=(1e-5, 1e5)
        Bounds for length scale.
    """

    def __init__(
        self,
        length_scale: float = 1.0,
        nu: float = 1.5,
        length_scale_bounds: Tuple[float, float] = (1e-5, 1e5),
    ):
        self.length_scale = length_scale
        self.nu = nu
        self.length_scale_bounds = length_scale_bounds

    def __call__(self, X: np.ndarray, Y: np.ndarray = None) -> np.ndarray:
        from scipy.special import kv, gamma

        if Y is None:
            dists = squareform(pdist(X, metric='euclidean'))
        else:
            dists = cdist(X, Y, metric='euclidean')

        dists = dists / self.length_scale

        if self.nu == 0.5:
            K = np.exp(-dists)
        elif self.nu == 1.5:
            K = (1 + np.sqrt(3) * dists) * np.exp(-np.sqrt(3) * dists)
        elif self.nu == 2.5:
            K = (1 + np.sqrt(5) * dists + 5/3 * dists**2) * np.exp(-np.sqrt(5) * dists)
        else:
            # General case
            K = np.zeros_like(dists)
            nonzero = dists > 0
            sqrt_2nu = np.sqrt(2 * self.nu) * dists[nonzero]
            K[nonzero] = (
                2 ** (1 - self.nu) / gamma(self.nu)
                * sqrt_2nu ** self.nu
                * kv(self.nu, sqrt_2nu)
            )
            K[~nonzero] = 1

        return K

    def diag(self, X: np.ndarray) -> np.ndarray:
        return np.ones(X.shape[0])

    def __repr__(self) -> str:
        return f"Matern(length_scale={self.length_scale}, nu={self.nu})"


class RationalQuadratic(Kernel):
    """
    Rational Quadratic kernel.

    k(x, y) = (1 + ||x-y||^2 / (2 * alpha * length_scale^2))^(-alpha)

    Parameters
    ----------
    length_scale : float, default=1.0
        The length scale.
    alpha : float, default=1.0
        The scale mixture parameter.
    """

    def __init__(
        self,
        length_scale: float = 1.0,
        alpha: float = 1.0,
        length_scale_bounds: Tuple[float, float] = (1e-5, 1e5),
        alpha_bounds: Tuple[float, float] = (1e-5, 1e5),
    ):
        self.length_scale = length_scale
        self.alpha = alpha
        self.length_scale_bounds = length_scale_bounds
        self.alpha_bounds = alpha_bounds

    def __call__(self, X: np.ndarray, Y: np.ndarray = None) -> np.ndarray:
        if Y is None:
            dists = squareform(pdist(X, metric='sqeuclidean'))
        else:
            dists = cdist(X, Y, metric='sqeuclidean')

        tmp = dists / (2 * self.alpha * self.length_scale ** 2)
        return (1 + tmp) ** (-self.alpha)

    def diag(self, X: np.ndarray) -> np.ndarray:
        return np.ones(X.shape[0])

    def __repr__(self) -> str:
        return f"RationalQuadratic(length_scale={self.length_scale}, alpha={self.alpha})"


class ExpSineSquared(Kernel):
    """
    Periodic kernel (Exp-Sine-Squared).

    k(x, y) = exp(-2 * sin^2(pi * ||x-y|| / periodicity) / length_scale^2)

    Parameters
    ----------
    length_scale : float, default=1.0
        The length scale.
    periodicity : float, default=1.0
        The periodicity.
    """

    def __init__(
        self,
        length_scale: float = 1.0,
        periodicity: float = 1.0,
        length_scale_bounds: Tuple[float, float] = (1e-5, 1e5),
        periodicity_bounds: Tuple[float, float] = (1e-5, 1e5),
    ):
        self.length_scale = length_scale
        self.periodicity = periodicity
        self.length_scale_bounds = length_scale_bounds
        self.periodicity_bounds = periodicity_bounds

    def __call__(self, X: np.ndarray, Y: np.ndarray = None) -> np.ndarray:
        if Y is None:
            dists = squareform(pdist(X, metric='euclidean'))
        else:
            dists = cdist(X, Y, metric='euclidean')

        arg = np.pi * dists / self.periodicity
        sin_arg = np.sin(arg)

        return np.exp(-2 * sin_arg ** 2 / self.length_scale ** 2)

    def diag(self, X: np.ndarray) -> np.ndarray:
        return np.ones(X.shape[0])

    def __repr__(self) -> str:
        return f"ExpSineSquared(length_scale={self.length_scale}, periodicity={self.periodicity})"


class DotProduct(Kernel):
    """
    Dot-Product kernel.

    k(x, y) = sigma_0^2 + x @ y.T

    Parameters
    ----------
    sigma_0 : float, default=1.0
        Inhomogeneity parameter.
    """

    def __init__(
        self,
        sigma_0: float = 1.0,
        sigma_0_bounds: Tuple[float, float] = (1e-5, 1e5),
    ):
        self.sigma_0 = sigma_0
        self.sigma_0_bounds = sigma_0_bounds

    def __call__(self, X: np.ndarray, Y: np.ndarray = None) -> np.ndarray:
        if Y is None:
            Y = X
        return self.sigma_0 ** 2 + X @ Y.T

    def diag(self, X: np.ndarray) -> np.ndarray:
        return self.sigma_0 ** 2 + np.sum(X ** 2, axis=1)

    def __repr__(self) -> str:
        return f"DotProduct(sigma_0={self.sigma_0})"


class WhiteKernel(Kernel):
    """
    White noise kernel.

    k(x, y) = noise_level if x == y else 0

    Parameters
    ----------
    noise_level : float, default=1.0
        Noise level.
    """

    def __init__(
        self,
        noise_level: float = 1.0,
        noise_level_bounds: Tuple[float, float] = (1e-5, 1e5),
    ):
        self.noise_level = noise_level
        self.noise_level_bounds = noise_level_bounds

    def __call__(self, X: np.ndarray, Y: np.ndarray = None) -> np.ndarray:
        if Y is None:
            return self.noise_level * np.eye(X.shape[0])
        else:
            return np.zeros((X.shape[0], Y.shape[0]))

    def diag(self, X: np.ndarray) -> np.ndarray:
        return self.noise_level * np.ones(X.shape[0])

    def __repr__(self) -> str:
        return f"WhiteKernel(noise_level={self.noise_level})"


class ConstantKernel(Kernel):
    """
    Constant kernel.

    k(x, y) = constant_value

    Parameters
    ----------
    constant_value : float, default=1.0
        The constant value.
    """

    def __init__(
        self,
        constant_value: float = 1.0,
        constant_value_bounds: Tuple[float, float] = (1e-5, 1e5),
    ):
        self.constant_value = constant_value
        self.constant_value_bounds = constant_value_bounds

    def __call__(self, X: np.ndarray, Y: np.ndarray = None) -> np.ndarray:
        n_X = X.shape[0]
        n_Y = Y.shape[0] if Y is not None else n_X
        return self.constant_value * np.ones((n_X, n_Y))

    def diag(self, X: np.ndarray) -> np.ndarray:
        return self.constant_value * np.ones(X.shape[0])

    def __repr__(self) -> str:
        return f"ConstantKernel(constant_value={self.constant_value})"


class Sum(Kernel):
    """Sum of two kernels."""

    def __init__(self, k1: Kernel, k2: Kernel):
        self.k1 = k1
        self.k2 = k2

    def __call__(self, X: np.ndarray, Y: np.ndarray = None) -> np.ndarray:
        return self.k1(X, Y) + self.k2(X, Y)

    def diag(self, X: np.ndarray) -> np.ndarray:
        return self.k1.diag(X) + self.k2.diag(X)

    def __repr__(self) -> str:
        return f"{self.k1} + {self.k2}"


class Product(Kernel):
    """Product of two kernels."""

    def __init__(self, k1, k2):
        self.k1 = k1 if isinstance(k1, Kernel) else ConstantKernel(k1)
        self.k2 = k2 if isinstance(k2, Kernel) else ConstantKernel(k2)

    def __call__(self, X: np.ndarray, Y: np.ndarray = None) -> np.ndarray:
        return self.k1(X, Y) * self.k2(X, Y)

    def diag(self, X: np.ndarray) -> np.ndarray:
        return self.k1.diag(X) * self.k2.diag(X)

    def __repr__(self) -> str:
        return f"{self.k1} * {self.k2}"
