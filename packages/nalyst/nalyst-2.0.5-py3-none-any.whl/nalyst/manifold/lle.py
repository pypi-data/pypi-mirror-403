"""
Locally Linear Embedding.
"""

from __future__ import annotations

from typing import Optional, Literal

import numpy as np
from scipy import linalg
from scipy.spatial.distance import cdist

from nalyst.core.foundation import BaseLearner, TransformerMixin
from nalyst.core.validation import check_array, check_is_trained


class LocallyLinearEmbedding(TransformerMixin, BaseLearner):
    """
    Locally Linear Embedding.

    Parameters
    ----------
    n_neighbors : int, default=5
        Number of neighbors to consider.
    n_components : int, default=2
        Number of coordinates.
    reg : float, default=1e-3
        Regularization constant.
    eigen_solver : {"auto", "arpack", "dense"}, default="auto"
        Eigensolver to use.
    tol : float, default=1e-6
        Tolerance for eigensolver.
    max_iter : int, default=100
        Maximum iterations for arpack.
    method : {"standard", "hessian", "modified", "ltsa"}, default="standard"
        Algorithm variant.
    hessian_tol : float, default=1e-4
        Tolerance for Hessian eigenmapping.
    modified_tol : float, default=1e-12
        Tolerance for modified LLE.
    random_state : int, optional
        Random seed.

    Attributes
    ----------
    embedding_ : ndarray of shape (n_samples, n_components)
        Stores the embedding vectors.
    reconstruction_error_ : float
        Reconstruction error.

    Examples
    --------
    >>> from nalyst.manifold import LocallyLinearEmbedding
    >>> X = np.random.randn(100, 10)
    >>> lle = LocallyLinearEmbedding(n_components=2)
    >>> X_embedded = lle.train_apply(X)
    """

    def __init__(
        self,
        n_neighbors: int = 5,
        *,
        n_components: int = 2,
        reg: float = 1e-3,
        eigen_solver: Literal["auto", "arpack", "dense"] = "auto",
        tol: float = 1e-6,
        max_iter: int = 100,
        method: Literal["standard", "hessian", "modified", "ltsa"] = "standard",
        hessian_tol: float = 1e-4,
        modified_tol: float = 1e-12,
        random_state: Optional[int] = None,
    ):
        self.n_neighbors = n_neighbors
        self.n_components = n_components
        self.reg = reg
        self.eigen_solver = eigen_solver
        self.tol = tol
        self.max_iter = max_iter
        self.method = method
        self.hessian_tol = hessian_tol
        self.modified_tol = modified_tol
        self.random_state = random_state

    def train(self, X: np.ndarray, y=None) -> "LocallyLinearEmbedding":
        """
        Compute the embedding.

        Parameters
        ----------
        X : ndarray of shape (n_samples, n_features)
            Training data.
        y : ignored

        Returns
        -------
        self : LocallyLinearEmbedding
            Fitted estimator.
        """
        X = check_array(X)
        self._train_X = X
        n_samples, n_features = X.shape

        if self.random_state is not None:
            np.random.seed(self.random_state)

        # Find k-nearest neighbors
        distances = cdist(X, X)
        neighbors = np.argsort(distances, axis=1)[:, 1:self.n_neighbors + 1]

        # Compute reconstruction weights
        W = np.zeros((n_samples, n_samples))

        for i in range(n_samples):
            nbrs = neighbors[i]
            Z = X[nbrs] - X[i]

            # Compute local covariance
            C = np.dot(Z, Z.T)

            # Regularize
            C += self.reg * np.eye(self.n_neighbors) * np.trace(C)

            # Solve for weights
            w = linalg.solve(C, np.ones(self.n_neighbors))
            w /= w.sum()

            W[i, nbrs] = w

        # Compute embedding
        # M = (I - W)^T @ (I - W)
        M = np.eye(n_samples) - W
        M = np.dot(M.T, M)

        # Eigendecomposition
        eigenvalues, eigenvectors = linalg.eigh(M)

        # Select smallest non-zero eigenvalues
        idx = np.argsort(eigenvalues)
        eigenvalues = eigenvalues[idx]
        eigenvectors = eigenvectors[:, idx]

        # Skip first (zero) eigenvalue
        self.embedding_ = eigenvectors[:, 1:self.n_components + 1]

        # Compute reconstruction error
        self.reconstruction_error_ = np.sum(eigenvalues[1:self.n_components + 1])

        return self

    def apply(self, X: np.ndarray) -> np.ndarray:
        """
        Transform new data.

        Parameters
        ----------
        X : ndarray of shape (n_samples, n_features)
            Data to transform.

        Returns
        -------
        X_new : ndarray of shape (n_samples, n_components)
            Transformed data.
        """
        check_is_trained(self, "embedding_")
        X = check_array(X)

        n_samples = X.shape[0]

        # Find neighbors in training data
        distances = cdist(X, self._train_X)
        neighbors = np.argsort(distances, axis=1)[:, :self.n_neighbors]

        # Compute weights
        X_new = np.zeros((n_samples, self.n_components))

        for i in range(n_samples):
            nbrs = neighbors[i]
            Z = self._train_X[nbrs] - X[i]

            C = np.dot(Z, Z.T)
            C += self.reg * np.eye(self.n_neighbors) * np.trace(C)

            w = linalg.solve(C, np.ones(self.n_neighbors))
            w /= w.sum()

            X_new[i] = np.dot(w, self.embedding_[nbrs])

        return X_new

    def train_apply(self, X: np.ndarray, y=None) -> np.ndarray:
        """
        Fit and transform X.

        Parameters
        ----------
        X : ndarray of shape (n_samples, n_features)
            Training data.
        y : ignored

        Returns
        -------
        X_new : ndarray of shape (n_samples, n_components)
            Embedded data.
        """
        self.train(X)
        return self.embedding_
