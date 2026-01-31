"""
Independent Component Analysis (ICA).
"""

from __future__ import annotations

from typing import Optional, Literal, Callable

import numpy as np
from scipy import linalg

from nalyst.core.foundation import BaseLearner, TransformerMixin
from nalyst.core.validation import check_array, check_is_trained


def _logcosh(x: np.ndarray, alpha: float = 1.0):
    """G(u) = log(cosh(u))"""
    gx = np.tanh(alpha * x)
    g_x = alpha * (1 - gx ** 2)
    return gx, g_x.mean(axis=-1)


def _exp(x: np.ndarray):
    """G(u) = -exp(-u^2/2)"""
    exp = np.exp(-(x ** 2) / 2)
    gx = x * exp
    g_x = (1 - x ** 2) * exp
    return gx, g_x.mean(axis=-1)


def _cube(x: np.ndarray):
    """G(u) = u^3 / 3"""
    return x ** 3, (3 * x ** 2).mean(axis=-1)


class FastICA(TransformerMixin, BaseLearner):
    """
    FastICA: Fast Independent Component Analysis.

    Parameters
    ----------
    n_components : int, optional
        Number of components. If None, all components are used.
    algorithm : {"parallel", "deflation"}, default="parallel"
        Apply parallel or deflational algorithm.
    whiten : bool, default=True
        Whether to whiten data before ICA.
    fun : {"logcosh", "exp", "cube"} or callable, default="logcosh"
        The functional form of G used in approximation to neg-entropy.
    fun_args : dict, optional
        Arguments to send to functional form.
    max_iter : int, default=200
        Maximum number of iterations.
    tol : float, default=1e-4
        Tolerance for convergence.
    w_init : ndarray, optional
        Initial unmixing matrix.
    random_state : int, optional
        Random seed.

    Attributes
    ----------
    components_ : ndarray of shape (n_components, n_features)
        Unmixing matrix W.
    mixing_ : ndarray of shape (n_features, n_components)
        Mixing matrix A = W^(-1).
    mean_ : ndarray of shape (n_features,)
        Mean of the data.
    n_iter_ : int
        Number of iterations.
    whitening_ : ndarray of shape (n_components, n_features)
        Whitening matrix.

    Examples
    --------
    >>> from nalyst.reduction import FastICA
    >>> X = np.random.randn(100, 3)
    >>> ica = FastICA(n_components=2)
    >>> ica.train(X)
    FastICA(n_components=2)
    >>> S = ica.apply(X)  # Recovered sources
    """

    def __init__(
        self,
        n_components: Optional[int] = None,
        *,
        algorithm: Literal["parallel", "deflation"] = "parallel",
        whiten: bool = True,
        fun: str = "logcosh",
        fun_args: Optional[dict] = None,
        max_iter: int = 200,
        tol: float = 1e-4,
        w_init: Optional[np.ndarray] = None,
        random_state: Optional[int] = None,
    ):
        self.n_components = n_components
        self.algorithm = algorithm
        self.whiten = whiten
        self.fun = fun
        self.fun_args = fun_args or {}
        self.max_iter = max_iter
        self.tol = tol
        self.w_init = w_init
        self.random_state = random_state

    def _get_fun(self) -> Callable:
        """Get the nonlinearity function."""
        if callable(self.fun):
            return self.fun
        elif self.fun == "logcosh":
            return lambda x: _logcosh(x, self.fun_args.get("alpha", 1.0))
        elif self.fun == "exp":
            return _exp
        elif self.fun == "cube":
            return _cube
        else:
            raise ValueError(f"Unknown function: {self.fun}")

    def train(self, X: np.ndarray, y=None) -> "FastICA":
        """
        Fit the model with X.

        Parameters
        ----------
        X : ndarray of shape (n_samples, n_features)
            Training data.
        y : ignored

        Returns
        -------
        self : FastICA
            Fitted transformer.
        """
        X = check_array(X)
        n_samples, n_features = X.shape

        if self.random_state is not None:
            np.random.seed(self.random_state)

        n_components = self.n_components or n_features

        # Center data
        self.mean_ = np.mean(X, axis=0)
        X_centered = X - self.mean_

        # Whiten data
        if self.whiten:
            X_white, self.whitening_ = self._whiten(X_centered, n_components)
        else:
            X_white = X_centered
            self.whitening_ = np.eye(n_features)

        # Initialize unmixing matrix
        if self.w_init is not None:
            W = self.w_init
        else:
            W = np.random.randn(n_components, n_components)

        # Orthogonalize
        W = self._sym_decorrelation(W)

        # Get nonlinearity
        g = self._get_fun()

        # Run ICA
        if self.algorithm == "parallel":
            W, n_iter = self._ica_parallel(X_white.T, W, g)
        else:
            W, n_iter = self._ica_deflation(X_white.T, W, g)

        self.n_iter_ = n_iter

        # Compute components and mixing matrix
        if self.whiten:
            self.components_ = np.dot(W, self.whitening_)
        else:
            self.components_ = W

        self.mixing_ = linalg.pinv(self.components_)

        return self

    def _whiten(self, X: np.ndarray, n_components: int):
        """Whiten data using PCA."""
        U, S, Vt = linalg.svd(X, full_matrices=False)

        K = (Vt[:n_components] / S[:n_components, np.newaxis]) * np.sqrt(len(X))
        X_white = np.dot(X, K.T)

        return X_white, K

    def _sym_decorrelation(self, W: np.ndarray) -> np.ndarray:
        """Symmetric decorrelation: W = (W @ W.T)^(-1/2) @ W"""
        s, u = linalg.eigh(np.dot(W, W.T))
        return np.dot(np.dot(u * (1.0 / np.sqrt(s)), u.T), W)

    def _ica_parallel(self, X: np.ndarray, W: np.ndarray, g: Callable):
        """Parallel FastICA algorithm."""
        n_components = W.shape[0]
        n_features, n_samples = X.shape

        for n_iter in range(self.max_iter):
            gwtx, g_wtx = g(np.dot(W, X))
            W_new = np.dot(gwtx, X.T) / n_samples - g_wtx[:, np.newaxis] * W
            W_new = self._sym_decorrelation(W_new)

            # Check convergence
            lim = np.max(np.abs(np.abs(np.diag(np.dot(W_new, W.T))) - 1))
            W = W_new

            if lim < self.tol:
                break

        return W, n_iter + 1

    def _ica_deflation(self, X: np.ndarray, W: np.ndarray, g: Callable):
        """Deflation FastICA algorithm."""
        n_components = W.shape[0]
        n_features, n_samples = X.shape

        for j in range(n_components):
            w = W[j].copy()

            for n_iter in range(self.max_iter):
                gwtx, g_wtx = g(np.dot(w, X))
                w_new = (X * gwtx).mean(axis=1) - g_wtx * w

                # Orthogonalize
                if j > 0:
                    w_new -= np.dot(np.dot(w_new, W[:j].T), W[:j])

                w_new /= np.linalg.norm(w_new)

                lim = np.abs(np.abs(np.dot(w_new, w)) - 1)
                w = w_new

                if lim < self.tol:
                    break

            W[j] = w

        return W, n_iter + 1

    def apply(self, X: np.ndarray) -> np.ndarray:
        """
        Recover the sources from X.

        Parameters
        ----------
        X : ndarray of shape (n_samples, n_features)
            Data to transform.

        Returns
        -------
        X_new : ndarray of shape (n_samples, n_components)
            Recovered sources.
        """
        check_is_trained(self, "components_")
        X = check_array(X)

        return np.dot(X - self.mean_, self.components_.T)

    def inverse_apply(self, X: np.ndarray) -> np.ndarray:
        """
        Transform data back to original space.

        Parameters
        ----------
        X : ndarray of shape (n_samples, n_components)
            Transformed data (sources).

        Returns
        -------
        X_original : ndarray of shape (n_samples, n_features)
            Reconstructed data.
        """
        check_is_trained(self, "mixing_")
        X = check_array(X)

        return np.dot(X, self.mixing_.T) + self.mean_
