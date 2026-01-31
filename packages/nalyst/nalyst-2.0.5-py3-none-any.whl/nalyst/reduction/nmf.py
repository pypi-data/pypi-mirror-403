"""
Non-negative Matrix Factorization (NMF).
"""

from __future__ import annotations

from typing import Optional, Literal

import numpy as np

from nalyst.core.foundation import BaseLearner, TransformerMixin
from nalyst.core.validation import check_array, check_is_trained


class NonNegativeMatrixFactorization(TransformerMixin, BaseLearner):
    """
    Non-negative Matrix Factorization (NMF).

    Finds two non-negative matrices (W, H) whose product approximates
    the non-negative matrix X.

    Parameters
    ----------
    n_components : int, optional
        Number of components.
    init : {"random", "nndsvd", "nndsvda", "nndsvdar"}, default="random"
        Method for initialization.
    solver : {"cd", "mu"}, default="cd"
        Solver: 'cd' for Coordinate Descent, 'mu' for Multiplicative Update.
    beta_loss : {"frobenius", "kullback-leibler", "itakura-saito"}, default="frobenius"
        Loss function for mu solver.
    tol : float, default=1e-4
        Tolerance for stopping condition.
    max_iter : int, default=200
        Maximum number of iterations.
    random_state : int, optional
        Random seed.
    alpha : float, default=0.0
        Constant for regularization.
    l1_ratio : float, default=0.0
        Regularization mixing parameter.
    shuffle : bool, default=False
        Whether to shuffle data for CD solver.

    Attributes
    ----------
    components_ : ndarray of shape (n_components, n_features)
        Non-negative components H.
    n_components_ : int
        Actual number of components.
    reconstruction_err_ : float
        Frobenius norm of difference between X and WH.
    n_iter_ : int
        Actual number of iterations.

    Examples
    --------
    >>> from nalyst.reduction import NonNegativeMatrixFactorization
    >>> X = [[1, 1, 2], [2, 1, 1], [3, 2, 2]]
    >>> nmf = NonNegativeMatrixFactorization(n_components=2)
    >>> nmf.train(X)
    NonNegativeMatrixFactorization(n_components=2)
    >>> W = nmf.apply(X)
    """

    def __init__(
        self,
        n_components: Optional[int] = None,
        *,
        init: Literal["random", "nndsvd", "nndsvda", "nndsvdar"] = "random",
        solver: Literal["cd", "mu"] = "cd",
        beta_loss: Literal["frobenius", "kullback-leibler", "itakura-saito"] = "frobenius",
        tol: float = 1e-4,
        max_iter: int = 200,
        random_state: Optional[int] = None,
        alpha: float = 0.0,
        l1_ratio: float = 0.0,
        shuffle: bool = False,
    ):
        self.n_components = n_components
        self.init = init
        self.solver = solver
        self.beta_loss = beta_loss
        self.tol = tol
        self.max_iter = max_iter
        self.random_state = random_state
        self.alpha = alpha
        self.l1_ratio = l1_ratio
        self.shuffle = shuffle

    def _initialize(self, X: np.ndarray, n_components: int):
        """Initialize W and H matrices."""
        n_samples, n_features = X.shape

        if self.random_state is not None:
            np.random.seed(self.random_state)

        if self.init == "random":
            avg = np.sqrt(X.mean() / n_components)
            W = np.abs(np.random.randn(n_samples, n_components)) * avg
            H = np.abs(np.random.randn(n_components, n_features)) * avg
        elif self.init.startswith("nndsvd"):
            # NNDSVD initialization
            U, S, Vt = np.linalg.svd(X, full_matrices=False)
            W = np.zeros((n_samples, n_components))
            H = np.zeros((n_components, n_features))

            W[:, 0] = np.sqrt(S[0]) * np.abs(U[:, 0])
            H[0, :] = np.sqrt(S[0]) * np.abs(Vt[0, :])

            for j in range(1, n_components):
                x, y = U[:, j], Vt[j, :]
                x_p, x_n = np.maximum(x, 0), np.abs(np.minimum(x, 0))
                y_p, y_n = np.maximum(y, 0), np.abs(np.minimum(y, 0))

                x_p_nrm, y_p_nrm = np.linalg.norm(x_p), np.linalg.norm(y_p)
                x_n_nrm, y_n_nrm = np.linalg.norm(x_n), np.linalg.norm(y_n)

                m_p, m_n = x_p_nrm * y_p_nrm, x_n_nrm * y_n_nrm

                if m_p > m_n:
                    u, v, sigma = x_p / x_p_nrm, y_p / y_p_nrm, m_p
                else:
                    u, v, sigma = x_n / x_n_nrm, y_n / y_n_nrm, m_n

                W[:, j] = np.sqrt(S[j] * sigma) * u
                H[j, :] = np.sqrt(S[j] * sigma) * v

            if self.init == "nndsvda":
                avg = X.mean()
                W[W == 0] = avg
                H[H == 0] = avg
            elif self.init == "nndsvdar":
                avg = X.mean()
                W[W == 0] = avg * np.random.rand(np.sum(W == 0))
                H[H == 0] = avg * np.random.rand(np.sum(H == 0))
        else:
            raise ValueError(f"Unknown init: {self.init}")

        return W, H

    def train(self, X: np.ndarray, y=None) -> "NonNegativeMatrixFactorization":
        """
        Learn NMF model for the data X.

        Parameters
        ----------
        X : ndarray of shape (n_samples, n_features)
            Training data (non-negative).
        y : ignored

        Returns
        -------
        self : NonNegativeMatrixFactorization
            Fitted model.
        """
        X = check_array(X)

        if np.any(X < 0):
            raise ValueError("NMF requires non-negative input")

        n_samples, n_features = X.shape
        n_components = self.n_components or n_features
        self.n_components_ = n_components

        W, H = self._initialize(X, n_components)

        if self.solver == "mu":
            W, H, n_iter = self._multiplicative_update(X, W, H)
        else:
            W, H, n_iter = self._coordinate_descent(X, W, H)

        self.components_ = H
        self._W = W
        self.n_iter_ = n_iter
        self.reconstruction_err_ = np.linalg.norm(X - np.dot(W, H), 'fro')

        return self

    def _multiplicative_update(self, X: np.ndarray, W: np.ndarray, H: np.ndarray):
        """Multiplicative update algorithm."""
        eps = np.finfo(float).eps

        for n_iter in range(1, self.max_iter + 1):
            # Update H
            numerator = np.dot(W.T, X)
            denominator = np.dot(np.dot(W.T, W), H) + eps
            H *= numerator / denominator

            # Update W
            numerator = np.dot(X, H.T)
            denominator = np.dot(W, np.dot(H, H.T)) + eps
            W *= numerator / denominator

            # Check convergence
            if n_iter > 1:
                err = np.linalg.norm(X - np.dot(W, H), 'fro')
                if n_iter > 2 and abs(prev_err - err) < self.tol:
                    break
                prev_err = err
            else:
                prev_err = np.linalg.norm(X - np.dot(W, H), 'fro')

        return W, H, n_iter

    def _coordinate_descent(self, X: np.ndarray, W: np.ndarray, H: np.ndarray):
        """Coordinate descent algorithm."""
        eps = np.finfo(float).eps
        n_samples, n_features = X.shape
        n_components = H.shape[0]

        indices = np.arange(n_components)

        for n_iter in range(1, self.max_iter + 1):
            if self.shuffle:
                np.random.shuffle(indices)

            # Update H (fix W)
            WtW = np.dot(W.T, W)
            WtX = np.dot(W.T, X)

            for j in indices:
                numerator = WtX[j] - np.dot(WtW[j], H) + WtW[j, j] * H[j]
                H[j] = np.maximum(numerator / (WtW[j, j] + eps), 0)

            # Update W (fix H)
            HHt = np.dot(H, H.T)
            XHt = np.dot(X, H.T)

            for j in indices:
                numerator = XHt[:, j] - np.dot(W, HHt[:, j]) + HHt[j, j] * W[:, j]
                W[:, j] = np.maximum(numerator / (HHt[j, j] + eps), 0)

            # Check convergence
            err = np.linalg.norm(X - np.dot(W, H), 'fro')
            if n_iter > 1 and abs(prev_err - err) < self.tol:
                break
            prev_err = err

        return W, H, n_iter

    def apply(self, X: np.ndarray) -> np.ndarray:
        """
        Transform data according to the fitted NMF model.

        Parameters
        ----------
        X : ndarray of shape (n_samples, n_features)
            Data to transform.

        Returns
        -------
        W : ndarray of shape (n_samples, n_components)
            Transformed data.
        """
        check_is_trained(self, "components_")
        X = check_array(X)

        # Solve for W: X  W @ H
        H = self.components_
        W = np.linalg.lstsq(H.T, X.T, rcond=None)[0].T
        W = np.maximum(W, 0)

        return W

    def inverse_apply(self, W: np.ndarray) -> np.ndarray:
        """
        Transform data back to original space.

        Parameters
        ----------
        W : ndarray of shape (n_samples, n_components)
            Transformed data.

        Returns
        -------
        X : ndarray of shape (n_samples, n_features)
            Reconstructed data.
        """
        check_is_trained(self, "components_")
        W = check_array(W)

        return np.dot(W, self.components_)
