"""
Spectral Embedding.
"""

from __future__ import annotations

from typing import Optional, Literal

import numpy as np
from scipy import linalg
from scipy.spatial.distance import cdist

from nalyst.core.foundation import BaseLearner
from nalyst.core.validation import check_array, check_is_trained


class SpectralEmbedding(BaseLearner):
    """
    Spectral Embedding for non-linear dimensionality reduction.

    Parameters
    ----------
    n_components : int, default=2
        Dimension of the projected subspace.
    affinity : {"nearest_neighbors", "rbf", "precomputed"}, default="nearest_neighbors"
        How to construct the affinity matrix.
    gamma : float, optional
        Kernel coefficient for rbf kernel.
    random_state : int, optional
        Random seed.
    eigen_solver : {"arpack", "lobpcg", "amg"}, default=None
        Eigenvalue decomposition strategy.
    n_neighbors : int, default=None
        Number of nearest neighbors for building affinity matrix.

    Attributes
    ----------
    embedding_ : ndarray of shape (n_samples, n_components)
        Spectral embedding of the training matrix.
    affinity_matrix_ : ndarray of shape (n_samples, n_samples)
        Affinity matrix computed from samples.

    Examples
    --------
    >>> from nalyst.manifold import SpectralEmbedding
    >>> X = np.random.randn(100, 10)
    >>> se = SpectralEmbedding(n_components=2)
    >>> X_embedded = se.train_apply(X)
    """

    def __init__(
        self,
        n_components: int = 2,
        *,
        affinity: Literal["nearest_neighbors", "rbf", "precomputed"] = "nearest_neighbors",
        gamma: Optional[float] = None,
        random_state: Optional[int] = None,
        eigen_solver: Optional[str] = None,
        n_neighbors: Optional[int] = None,
    ):
        self.n_components = n_components
        self.affinity = affinity
        self.gamma = gamma
        self.random_state = random_state
        self.eigen_solver = eigen_solver
        self.n_neighbors = n_neighbors

    def _compute_affinity(self, X: np.ndarray) -> np.ndarray:
        """Compute affinity matrix."""
        n_samples = X.shape[0]

        if self.affinity == "precomputed":
            return X

        elif self.affinity == "rbf":
            gamma = self.gamma or (1.0 / X.shape[1])
            distances = cdist(X, X, metric='sqeuclidean')
            return np.exp(-gamma * distances)

        else:  # nearest_neighbors
            n_neighbors = self.n_neighbors or int(np.sqrt(n_samples))
            distances = cdist(X, X)

            # Build connectivity matrix
            affinity = np.zeros((n_samples, n_samples))

            for i in range(n_samples):
                indices = np.argsort(distances[i])[1:n_neighbors + 1]
                for j in indices:
                    affinity[i, j] = 1
                    affinity[j, i] = 1

            return affinity

    def train(self, X: np.ndarray, y=None) -> "SpectralEmbedding":
        """
        Fit the model from data.

        Parameters
        ----------
        X : ndarray of shape (n_samples, n_features)
            Training data.
        y : ignored

        Returns
        -------
        self : SpectralEmbedding
            Fitted estimator.
        """
        X = check_array(X)
        self._train_X = X

        if self.random_state is not None:
            np.random.seed(self.random_state)

        # Compute affinity matrix
        self.affinity_matrix_ = self._compute_affinity(X)

        # Compute normalized Laplacian
        degree = np.sum(self.affinity_matrix_, axis=1)
        D_inv_sqrt = np.diag(1.0 / np.sqrt(degree + 1e-10))

        L = np.eye(len(X)) - np.dot(np.dot(D_inv_sqrt, self.affinity_matrix_), D_inv_sqrt)

        # Eigendecomposition
        eigenvalues, eigenvectors = linalg.eigh(L)

        # Sort by eigenvalue (ascending)
        idx = np.argsort(eigenvalues)
        eigenvalues = eigenvalues[idx]
        eigenvectors = eigenvectors[:, idx]

        # Skip first eigenvalue (should be ~0)
        self.embedding_ = eigenvectors[:, 1:self.n_components + 1]

        return self

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
            Spectral embedding.
        """
        self.train(X)
        return self.embedding_
