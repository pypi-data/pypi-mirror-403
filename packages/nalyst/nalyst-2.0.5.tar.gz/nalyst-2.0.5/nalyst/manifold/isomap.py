"""
Isomap Embedding.
"""

from __future__ import annotations

from typing import Optional, Literal

import numpy as np
from scipy.spatial.distance import cdist
from scipy.sparse.csgraph import shortest_path

from nalyst.core.foundation import BaseLearner, TransformerMixin
from nalyst.core.validation import check_array, check_is_trained


class Isomap(TransformerMixin, BaseLearner):
    """
    Isometric Mapping.

    Non-linear dimensionality reduction through geodesic distances.

    Parameters
    ----------
    n_neighbors : int, default=5
        Number of neighbors for each point.
    n_components : int, default=2
        Number of coordinates for the manifold.
    eigen_solver : {"auto", "arpack", "dense"}, default="auto"
        Eigensolver to use.
    tol : float, default=0.0
        Convergence tolerance.
    max_iter : int, optional
        Maximum number of iterations.
    path_method : {"auto", "FW", "D"}, default="auto"
        Method for computing shortest paths.
    neighbors_algorithm : {"auto", "brute", "ball_tree", "kd_tree"}, default="auto"
        Algorithm for nearest neighbor search.
    metric : str, default="minkowski"
        Distance metric.
    p : int, default=2
        Parameter for Minkowski metric.

    Attributes
    ----------
    embedding_ : ndarray of shape (n_samples, n_components)
        Stores the embedding.
    kernel_pca_ : object
        Kernel PCA model.
    dist_matrix_ : ndarray of shape (n_samples, n_samples)
        Geodesic distance matrix.

    Examples
    --------
    >>> from nalyst.manifold import Isomap
    >>> X = np.random.randn(100, 10)
    >>> iso = Isomap(n_components=2)
    >>> X_embedded = iso.train_apply(X)
    """

    def __init__(
        self,
        n_neighbors: int = 5,
        *,
        n_components: int = 2,
        eigen_solver: Literal["auto", "arpack", "dense"] = "auto",
        tol: float = 0.0,
        max_iter: Optional[int] = None,
        path_method: Literal["auto", "FW", "D"] = "auto",
        neighbors_algorithm: Literal["auto", "brute", "ball_tree", "kd_tree"] = "auto",
        metric: str = "minkowski",
        p: int = 2,
    ):
        self.n_neighbors = n_neighbors
        self.n_components = n_components
        self.eigen_solver = eigen_solver
        self.tol = tol
        self.max_iter = max_iter
        self.path_method = path_method
        self.neighbors_algorithm = neighbors_algorithm
        self.metric = metric
        self.p = p

    def train(self, X: np.ndarray, y=None) -> "Isomap":
        """
        Compute the embedding.

        Parameters
        ----------
        X : ndarray of shape (n_samples, n_features)
            Input data.
        y : ignored

        Returns
        -------
        self : Isomap
            Fitted estimator.
        """
        X = check_array(X)
        self._train_X = X
        n_samples = X.shape[0]

        # Compute pairwise distances
        if self.metric == "minkowski":
            distances = cdist(X, X, metric="minkowski", p=self.p)
        else:
            distances = cdist(X, X, metric=self.metric)

        # Build k-nearest neighbors graph
        graph = np.full((n_samples, n_samples), np.inf)

        for i in range(n_samples):
            # Get k nearest neighbors
            indices = np.argsort(distances[i])[:self.n_neighbors + 1]
            for j in indices:
                if i != j:
                    graph[i, j] = distances[i, j]

        # Make symmetric
        graph = np.minimum(graph, graph.T)

        # Compute shortest paths
        if self.path_method == "FW":
            self.dist_matrix_ = shortest_path(graph, method="FW")
        elif self.path_method == "D":
            self.dist_matrix_ = shortest_path(graph, method="D")
        else:
            self.dist_matrix_ = shortest_path(graph)

        # Apply MDS to geodesic distances
        self.embedding_ = self._mds_embedding(self.dist_matrix_)

        return self

    def _mds_embedding(self, D: np.ndarray) -> np.ndarray:
        """Compute MDS embedding from distance matrix."""
        n_samples = D.shape[0]

        # Double centering
        D_sq = D ** 2
        row_mean = D_sq.mean(axis=1, keepdims=True)
        col_mean = D_sq.mean(axis=0, keepdims=True)
        total_mean = D_sq.mean()

        B = -0.5 * (D_sq - row_mean - col_mean + total_mean)

        # Eigendecomposition
        eigenvalues, eigenvectors = np.linalg.eigh(B)

        # Sort by decreasing eigenvalue
        idx = np.argsort(eigenvalues)[::-1]
        eigenvalues = eigenvalues[idx]
        eigenvectors = eigenvectors[:, idx]

        # Select top components
        eigenvalues = eigenvalues[:self.n_components]
        eigenvectors = eigenvectors[:, :self.n_components]

        # Handle negative eigenvalues
        eigenvalues = np.maximum(eigenvalues, 0)

        # Compute embedding
        return eigenvectors * np.sqrt(eigenvalues)

    def apply(self, X: np.ndarray) -> np.ndarray:
        """
        Transform X.

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

        # Compute distances to training points
        if self.metric == "minkowski":
            distances = cdist(X, self._train_X, metric="minkowski", p=self.p)
        else:
            distances = cdist(X, self._train_X, metric=self.metric)

        # Find k nearest neighbors and interpolate
        n_samples = X.shape[0]
        X_new = np.zeros((n_samples, self.n_components))

        for i in range(n_samples):
            indices = np.argsort(distances[i])[:self.n_neighbors]
            weights = 1.0 / (distances[i, indices] + 1e-10)
            weights /= weights.sum()
            X_new[i] = np.sum(weights[:, np.newaxis] * self.embedding_[indices], axis=0)

        return X_new

    def train_apply(self, X: np.ndarray, y=None) -> np.ndarray:
        """
        Fit and transform X.

        Parameters
        ----------
        X : ndarray of shape (n_samples, n_features)
            Input data.
        y : ignored

        Returns
        -------
        X_new : ndarray of shape (n_samples, n_components)
            Transformed data.
        """
        self.train(X)
        return self.embedding_

    def reconstruction_error(self) -> float:
        """
        Compute reconstruction error.

        Returns
        -------
        error : float
            Reconstruction error.
        """
        check_is_trained(self, "embedding_")

        # Compute distances in embedding space
        embedded_distances = cdist(self.embedding_, self.embedding_)

        # Compare with geodesic distances
        error = np.sum((self.dist_matrix_ - embedded_distances) ** 2)

        return error
