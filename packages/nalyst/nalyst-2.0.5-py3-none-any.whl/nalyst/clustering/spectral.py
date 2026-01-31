"""
Spectral clustering algorithms.

Uses graph-based methods for clustering by finding
connected components in a similarity graph.
"""

from __future__ import annotations

from typing import Optional, Union, Literal, Callable

import numpy as np
from scipy.spatial.distance import cdist

from nalyst.core.foundation import BaseLearner, ClusterMixin
from nalyst.core.validation import (
    check_array,
    check_is_trained,
    check_random_state,
)
from nalyst.core.tags import LearnerTags, TargetTags


class SpectralClustering(ClusterMixin, BaseLearner):
    """
    Spectral Clustering algorithm.

    Performs clustering by embedding data in the eigenspace
    of the graph Laplacian.

    Parameters
    ----------
    n_clusters : int, default=8
        Number of clusters.
    eigen_solver : {"arpack", "lobpcg", "amg"}, optional
        Eigenvalue solver.
    n_components : int, optional
        Number of eigenvectors. Defaults to n_clusters.
    random_state : int, optional
        Random seed.
    n_init : int, default=10
        Number of k-means initializations.
    gamma : float, default=1.0
        Kernel coefficient for RBF.
    affinity : str or callable, default="rbf"
        Affinity matrix type: "rbf", "nearest_neighbors", "precomputed".
    n_neighbors : int, default=10
        Number of neighbors for affinity.
    eigen_tol : float, default=0.0
        Tolerance for eigenvalue solver.
    assign_labels : {"kmeans", "discretize"}, default="kmeans"
        Strategy for assigning labels.
    degree : float, default=3
        Degree for polynomial kernel.
    coef0 : float, default=1
        Zero coefficient for polynomial kernel.
    kernel_params : dict, optional
        Parameters for kernel function.
    n_jobs : int, optional
        Number of parallel jobs.
    verbose : bool, default=False
        Verbosity.

    Attributes
    ----------
    labels_ : ndarray of shape (n_samples,)
        Cluster labels.
    affinity_matrix_ : ndarray
        Affinity matrix.
    n_features_in_ : int
        Number of features.

    Examples
    --------
    >>> import numpy as np
    >>> from nalyst.clustering import SpectralClustering
    >>> X = np.array([[1, 1], [2, 1], [1, 0], [4, 7], [3, 5], [3, 6]])
    >>> clustering = SpectralClustering(n_clusters=2, random_state=42)
    >>> clustering.train(X)
    SpectralClustering(n_clusters=2, random_state=42)
    >>> clustering.labels_
    array([1, 1, 1, 0, 0, 0])
    """

    def __init__(
        self,
        n_clusters: int = 8,
        *,
        eigen_solver: Optional[str] = None,
        n_components: Optional[int] = None,
        random_state: Optional[int] = None,
        n_init: int = 10,
        gamma: float = 1.0,
        affinity: Union[str, Callable] = "rbf",
        n_neighbors: int = 10,
        eigen_tol: float = 0.0,
        assign_labels: Literal["kmeans", "discretize"] = "kmeans",
        degree: float = 3,
        coef0: float = 1,
        kernel_params: Optional[dict] = None,
        n_jobs: Optional[int] = None,
        verbose: bool = False,
    ):
        self.n_clusters = n_clusters
        self.eigen_solver = eigen_solver
        self.n_components = n_components
        self.random_state = random_state
        self.n_init = n_init
        self.gamma = gamma
        self.affinity = affinity
        self.n_neighbors = n_neighbors
        self.eigen_tol = eigen_tol
        self.assign_labels = assign_labels
        self.degree = degree
        self.coef0 = coef0
        self.kernel_params = kernel_params
        self.n_jobs = n_jobs
        self.verbose = verbose

    def _compute_affinity_matrix(self, X: np.ndarray) -> np.ndarray:
        """Compute affinity matrix."""
        n_samples = X.shape[0]

        if self.affinity == "precomputed":
            return X

        elif self.affinity == "rbf":
            # RBF (Gaussian) kernel
            distances_sq = cdist(X, X, metric="sqeuclidean")
            return np.exp(-self.gamma * distances_sq)

        elif self.affinity == "nearest_neighbors":
            # k-NN affinity
            distances = cdist(X, X, metric="euclidean")
            affinity = np.zeros((n_samples, n_samples))

            for i in range(n_samples):
                # Get k nearest neighbors
                sorted_indices = np.argsort(distances[i])
                neighbors = sorted_indices[1:self.n_neighbors + 1]

                for j in neighbors:
                    affinity[i, j] = 1.0
                    affinity[j, i] = 1.0  # Symmetric

            return affinity

        elif callable(self.affinity):
            # Custom affinity function
            return self.affinity(X)

        else:
            raise ValueError(f"Unknown affinity: {self.affinity}")

    def _compute_laplacian(
        self,
        affinity: np.ndarray,
        normalized: bool = True,
    ) -> np.ndarray:
        """Compute graph Laplacian."""
        # Degree matrix
        degree = np.diag(np.sum(affinity, axis=1))

        # Laplacian
        laplacian = degree - affinity

        if normalized:
            # Normalized Laplacian: D^(-1/2) L D^(-1/2)
            d_inv_sqrt = np.diag(1.0 / np.sqrt(np.diag(degree) + 1e-10))
            laplacian = d_inv_sqrt @ laplacian @ d_inv_sqrt

        return laplacian

    def _spectral_embedding(
        self,
        laplacian: np.ndarray,
        n_components: int,
    ) -> np.ndarray:
        """Compute spectral embedding."""
        # Compute eigenvalues and eigenvectors
        eigenvalues, eigenvectors = np.linalg.eigh(laplacian)

        # Select smallest eigenvalues (skip first if normalized)
        indices = np.argsort(eigenvalues)[:n_components]

        embedding = eigenvectors[:, indices]

        # Normalize rows
        norms = np.linalg.norm(embedding, axis=1, keepdims=True)
        norms[norms == 0] = 1
        embedding = embedding / norms

        return embedding

    def _kmeans_labels(
        self,
        embedding: np.ndarray,
        rng: np.random.RandomState,
    ) -> np.ndarray:
        """Assign labels using k-means."""
        from nalyst.clustering.kmeans import KMeansClustering

        best_labels = None
        best_inertia = np.inf

        for _ in range(self.n_init):
            kmeans = KMeansClustering(
                n_clusters=self.n_clusters,
                random_state=rng.randint(np.iinfo(np.int32).max),
                n_init=1,
            )
            kmeans.train(embedding)

            if kmeans.inertia_ < best_inertia:
                best_inertia = kmeans.inertia_
                best_labels = kmeans.labels_

        return best_labels

    def _discretize_labels(
        self,
        embedding: np.ndarray,
        rng: np.random.RandomState,
    ) -> np.ndarray:
        """Assign labels using discretization."""
        n_samples, n_components = embedding.shape

        # Normalize embedding
        norms = np.linalg.norm(embedding, axis=1, keepdims=True)
        norms[norms == 0] = 1
        vectors = embedding / norms

        # Initialize with random rotation
        rotation = rng.randn(n_components, self.n_clusters)
        rotation, _ = np.linalg.qr(rotation)

        # Iteratively refine
        for _ in range(50):
            # Assign to nearest centroid direction
            similarities = vectors @ rotation
            labels = np.argmax(similarities, axis=1)

            # Update rotation
            for k in range(self.n_clusters):
                mask = labels == k
                if np.any(mask):
                    cluster_vectors = vectors[mask]
                    rotation[:, k] = cluster_vectors.mean(axis=0)

            # Orthonormalize
            rotation, _ = np.linalg.qr(rotation)

        return labels

    def train(self, X: np.ndarray, y=None) -> "SpectralClustering":
        """
        Perform spectral clustering.

        Parameters
        ----------
        X : array-like of shape (n_samples, n_features)
            Training data or precomputed affinity matrix.
        y : Ignored
            Not used.

        Returns
        -------
        self : SpectralClustering
        """
        X = check_array(X)

        if self.affinity != "precomputed":
            self.n_features_in_ = X.shape[1]

        rng = check_random_state(self.random_state)

        # Number of components
        n_components = self.n_components or self.n_clusters

        # Compute affinity matrix
        self.affinity_matrix_ = self._compute_affinity_matrix(X)

        # Compute Laplacian
        laplacian = self._compute_laplacian(self.affinity_matrix_)

        # Spectral embedding
        embedding = self._spectral_embedding(laplacian, n_components)

        # Assign labels
        if self.assign_labels == "kmeans":
            self.labels_ = self._kmeans_labels(embedding, rng)
        else:
            self.labels_ = self._discretize_labels(embedding, rng)

        return self

    def train_infer(self, X: np.ndarray, y=None) -> np.ndarray:
        """
        Perform spectral clustering and return labels.

        Parameters
        ----------
        X : array-like of shape (n_samples, n_features)
            Training data.
        y : Ignored
            Not used.

        Returns
        -------
        labels : ndarray of shape (n_samples,)
            Cluster labels.
        """
        return self.train(X, y).labels_

    def __nalyst_tags__(self) -> LearnerTags:
        return LearnerTags(
            learner_type="clusterer",
            target_tags=TargetTags(required=False),
        )
