"""
Base classes and utilities for SVM algorithms.
"""

from __future__ import annotations

from typing import Optional, Literal, Callable
from abc import abstractmethod

import numpy as np
from scipy.optimize import minimize

from nalyst.core.foundation import BaseLearner
from nalyst.core.validation import check_array


def linear_kernel(X: np.ndarray, Y: np.ndarray) -> np.ndarray:
    """Linear kernel: K(x, y) = x^T y"""
    return np.dot(X, Y.T)


def polynomial_kernel(
    X: np.ndarray,
    Y: np.ndarray,
    degree: int = 3,
    gamma: float = 1.0,
    coef0: float = 0.0,
) -> np.ndarray:
    """Polynomial kernel: K(x, y) = (gamma * x^T y + coef0)^degree"""
    return (gamma * np.dot(X, Y.T) + coef0) ** degree


def rbf_kernel(
    X: np.ndarray,
    Y: np.ndarray,
    gamma: float = 1.0,
) -> np.ndarray:
    """RBF kernel: K(x, y) = exp(-gamma * ||x - y||^2)"""
    X_sq = np.sum(X ** 2, axis=1).reshape(-1, 1)
    Y_sq = np.sum(Y ** 2, axis=1).reshape(1, -1)
    sq_dist = X_sq + Y_sq - 2 * np.dot(X, Y.T)
    return np.exp(-gamma * sq_dist)


def sigmoid_kernel(
    X: np.ndarray,
    Y: np.ndarray,
    gamma: float = 1.0,
    coef0: float = 0.0,
) -> np.ndarray:
    """Sigmoid kernel: K(x, y) = tanh(gamma * x^T y + coef0)"""
    return np.tanh(gamma * np.dot(X, Y.T) + coef0)


def get_kernel_function(
    kernel: str,
    degree: int = 3,
    gamma: float = 1.0,
    coef0: float = 0.0,
) -> Callable:
    """
    Get the kernel function by name.

    Parameters
    ----------
    kernel : str
        Kernel name: 'linear', 'poly', 'rbf', 'sigmoid'.
    degree : int, default=3
        Degree for polynomial kernel.
    gamma : float, default=1.0
        Gamma parameter.
    coef0 : float, default=0.0
        Independent term.

    Returns
    -------
    kernel_func : callable
        The kernel function.
    """
    if kernel == "linear":
        return linear_kernel
    elif kernel == "poly":
        return lambda X, Y: polynomial_kernel(X, Y, degree, gamma, coef0)
    elif kernel == "rbf":
        return lambda X, Y: rbf_kernel(X, Y, gamma)
    elif kernel == "sigmoid":
        return lambda X, Y: sigmoid_kernel(X, Y, gamma, coef0)
    else:
        raise ValueError(f"Unknown kernel: {kernel}")


class SVMBase(BaseLearner):
    """
    Base class for SVM algorithms.

    Parameters
    ----------
    kernel : str, default="rbf"
        Kernel type: 'linear', 'poly', 'rbf', 'sigmoid'.
    degree : int, default=3
        Degree of polynomial kernel.
    gamma : str or float, default="scale"
        Kernel coefficient.
    coef0 : float, default=0.0
        Independent term in kernel function.
    C : float, default=1.0
        Regularization parameter.
    tol : float, default=1e-3
        Tolerance for stopping criterion.
    max_iter : int, default=1000
        Maximum number of iterations.
    random_state : int, optional
        Random seed.
    """

    def __init__(
        self,
        kernel: str = "rbf",
        *,
        degree: int = 3,
        gamma: str = "scale",
        coef0: float = 0.0,
        C: float = 1.0,
        tol: float = 1e-3,
        max_iter: int = 1000,
        random_state: Optional[int] = None,
    ):
        self.kernel = kernel
        self.degree = degree
        self.gamma = gamma
        self.coef0 = coef0
        self.C = C
        self.tol = tol
        self.max_iter = max_iter
        self.random_state = random_state

    def _compute_gamma(self, X: np.ndarray) -> float:
        """Compute gamma value based on strategy."""
        if isinstance(self.gamma, (int, float)):
            return self.gamma
        elif self.gamma == "scale":
            var = X.var()
            return 1.0 / (X.shape[1] * var) if var != 0 else 1.0
        elif self.gamma == "auto":
            return 1.0 / X.shape[1]
        else:
            raise ValueError(f"Unknown gamma: {self.gamma}")

    def _get_kernel(self, X: np.ndarray) -> Callable:
        """Get kernel function with computed gamma."""
        gamma = self._compute_gamma(X)
        return get_kernel_function(self.kernel, self.degree, gamma, self.coef0)

    def _compute_kernel_matrix(self, X: np.ndarray, Y: Optional[np.ndarray] = None) -> np.ndarray:
        """Compute kernel matrix."""
        if Y is None:
            Y = X
        return self._kernel_func(X, Y)
