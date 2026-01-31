"""
K-Means clustering implementations.

Provides partitioning-based clustering algorithms that divide
data into k clusters by minimizing within-cluster variance.
"""

from __future__ import annotations

from typing import Optional, Union, Literal

import numpy as np

from nalyst.core.foundation import BaseLearner, ClusterMixin, TransformerMixin
from nalyst.core.validation import (
    check_array,
    check_is_trained,
    check_random_state,
)
from nalyst.core.tags import LearnerTags, TargetTags


def _euclidean_distances(X: np.ndarray, Y: np.ndarray) -> np.ndarray:
    """Compute pairwise Euclidean distances."""
    # Using the formula: ||x-y||^2 = ||x||^2 + ||y||^2 - 2*x.y
    X_norm_sq = np.sum(X ** 2, axis=1)[:, np.newaxis]
    Y_norm_sq = np.sum(Y ** 2, axis=1)[np.newaxis, :]
    distances_sq = X_norm_sq + Y_norm_sq - 2 * X @ Y.T
    distances_sq = np.maximum(distances_sq, 0)  # Handle numerical errors
    return np.sqrt(distances_sq)


def _kmeans_plusplus_init(
    X: np.ndarray,
    n_clusters: int,
    rng: np.random.RandomState,
    n_local_trials: int = None,
) -> np.ndarray:
    """K-means++ initialization."""
    n_samples, n_features = X.shape
    centers = np.empty((n_clusters, n_features))

    if n_local_trials is None:
        n_local_trials = 2 + int(np.log(n_clusters))

    # Choose first center uniformly at random
    center_id = rng.randint(n_samples)
    centers[0] = X[center_id]

    # Compute distances to first center
    closest_dist_sq = np.sum((X - centers[0]) ** 2, axis=1)
    current_pot = closest_dist_sq.sum()

    # Choose remaining centers
    for c in range(1, n_clusters):
        # Choose candidates
        rand_vals = rng.random(n_local_trials) * current_pot
        candidate_ids = np.searchsorted(
            np.cumsum(closest_dist_sq), rand_vals
        )
        candidate_ids = np.clip(candidate_ids, 0, n_samples - 1)

        # Evaluate candidates
        best_candidate = None
        best_pot = None

        for candidate_id in candidate_ids:
            new_dist_sq = np.sum((X - X[candidate_id]) ** 2, axis=1)
            new_pot = np.minimum(closest_dist_sq, new_dist_sq).sum()

            if best_candidate is None or new_pot < best_pot:
                best_candidate = candidate_id
                best_pot = new_pot

        centers[c] = X[best_candidate]
        closest_dist_sq = np.minimum(
            closest_dist_sq,
            np.sum((X - centers[c]) ** 2, axis=1)
        )
        current_pot = closest_dist_sq.sum()

    return centers


class KMeansClustering(ClusterMixin, TransformerMixin, BaseLearner):
    """
    K-Means clustering algorithm.

    Partitions data into k clusters by iteratively updating
    cluster centroids and reassigning points.

    Parameters
    ----------
    n_clusters : int, default=8
        Number of clusters.
    init : {"k-means++", "random"} or ndarray, default="k-means++"
        Initialization method.
    n_init : int or "auto", default="auto"
        Number of initializations.
    max_iter : int, default=300
        Maximum iterations per run.
    tol : float, default=1e-4
        Convergence tolerance.
    verbose : int, default=0
        Verbosity level.
    random_state : int, optional
        Random seed.
    copy_x : bool, default=True
        Copy input data.
    algorithm : {"lloyd", "elkan"}, default="lloyd"
        K-means algorithm variant.

    Attributes
    ----------
    cluster_centers_ : ndarray of shape (n_clusters, n_features)
        Coordinates of cluster centers.
    labels_ : ndarray of shape (n_samples,)
        Labels of each point.
    inertia_ : float
        Sum of squared distances to closest centroid.
    n_iter_ : int
        Number of iterations.
    n_features_in_ : int
        Number of features.

    Examples
    --------
    >>> import numpy as np
    >>> from nalyst.clustering import KMeansClustering
    >>> X = np.array([[1, 2], [1, 4], [1, 0], [10, 2], [10, 4], [10, 0]])
    >>> kmeans = KMeansClustering(n_clusters=2, random_state=42)
    >>> kmeans.train(X)
    KMeansClustering(n_clusters=2, random_state=42)
    >>> kmeans.labels_
    array([0, 0, 0, 1, 1, 1])
    >>> kmeans.infer([[0, 0], [12, 3]])
    array([0, 1])
    """

    def __init__(
        self,
        n_clusters: int = 8,
        *,
        init: Union[str, np.ndarray] = "k-means++",
        n_init: Union[int, str] = "auto",
        max_iter: int = 300,
        tol: float = 1e-4,
        verbose: int = 0,
        random_state: Optional[int] = None,
        copy_x: bool = True,
        algorithm: Literal["lloyd", "elkan"] = "lloyd",
    ):
        self.n_clusters = n_clusters
        self.init = init
        self.n_init = n_init
        self.max_iter = max_iter
        self.tol = tol
        self.verbose = verbose
        self.random_state = random_state
        self.copy_x = copy_x
        self.algorithm = algorithm

    def _init_centroids(
        self,
        X: np.ndarray,
        rng: np.random.RandomState,
    ) -> np.ndarray:
        """Initialize cluster centroids."""
        n_samples = X.shape[0]

        if isinstance(self.init, np.ndarray):
            return self.init.copy()
        elif self.init == "k-means++":
            return _kmeans_plusplus_init(X, self.n_clusters, rng)
        else:  # random
            indices = rng.choice(n_samples, self.n_clusters, replace=False)
            return X[indices].copy()

    def _assign_labels(
        self,
        X: np.ndarray,
        centers: np.ndarray,
    ) -> tuple:
        """Assign points to nearest centroid."""
        distances = _euclidean_distances(X, centers)
        labels = np.argmin(distances, axis=1)
        inertia = np.sum(np.min(distances, axis=1) ** 2)
        return labels, inertia

    def _update_centroids(
        self,
        X: np.ndarray,
        labels: np.ndarray,
        centers: np.ndarray,
    ) -> np.ndarray:
        """Update centroids to cluster means."""
        new_centers = np.zeros_like(centers)

        for k in range(self.n_clusters):
            mask = labels == k
            if np.any(mask):
                new_centers[k] = X[mask].mean(axis=0)
            else:
                # Empty cluster: reinitialize
                new_centers[k] = centers[k]

        return new_centers

    def _kmeans_single(
        self,
        X: np.ndarray,
        rng: np.random.RandomState,
    ) -> tuple:
        """Run a single K-means iteration."""
        centers = self._init_centroids(X, rng)

        for iteration in range(self.max_iter):
            # Assign labels
            labels, inertia = self._assign_labels(X, centers)

            # Update centroids
            new_centers = self._update_centroids(X, labels, centers)

            # Check convergence
            center_shift = np.sum((new_centers - centers) ** 2)
            centers = new_centers

            if self.verbose:
                print(f"Iteration {iteration + 1}, inertia: {inertia:.4f}")

            if center_shift < self.tol:
                break

        return centers, labels, inertia, iteration + 1

    def train(self, X: np.ndarray, y=None) -> "KMeansClustering":
        """
        Compute k-means clustering.

        Parameters
        ----------
        X : array-like of shape (n_samples, n_features)
            Training data.
        y : Ignored
            Not used.

        Returns
        -------
        self : KMeansClustering
        """
        X = check_array(X)
        if self.copy_x:
            X = X.copy()

        self.n_features_in_ = X.shape[1]

        rng = check_random_state(self.random_state)

        # Determine n_init
        if self.n_init == "auto":
            n_init = 10 if self.init == "random" else 1
        else:
            n_init = self.n_init

        best_inertia = None
        best_centers = None
        best_labels = None
        best_n_iter = None

        for i in range(n_init):
            centers, labels, inertia, n_iter = self._kmeans_single(X, rng)

            if best_inertia is None or inertia < best_inertia:
                best_inertia = inertia
                best_centers = centers
                best_labels = labels
                best_n_iter = n_iter

        self.cluster_centers_ = best_centers
        self.labels_ = best_labels
        self.inertia_ = best_inertia
        self.n_iter_ = best_n_iter

        return self

    def infer(self, X: np.ndarray) -> np.ndarray:
        """
        Predict cluster labels for samples.

        Parameters
        ----------
        X : array-like of shape (n_samples, n_features)
            Samples.

        Returns
        -------
        labels : ndarray of shape (n_samples,)
            Cluster labels.
        """
        check_is_trained(self)
        X = check_array(X)

        labels, _ = self._assign_labels(X, self.cluster_centers_)
        return labels

    def transform(self, X: np.ndarray) -> np.ndarray:
        """
        Transform X to cluster-distance space.

        Parameters
        ----------
        X : array-like of shape (n_samples, n_features)
            Samples.

        Returns
        -------
        distances : ndarray of shape (n_samples, n_clusters)
            Distances to each cluster center.
        """
        check_is_trained(self)
        X = check_array(X)

        return _euclidean_distances(X, self.cluster_centers_)

    def train_infer(self, X: np.ndarray, y=None) -> np.ndarray:
        """
        Compute clustering and return cluster labels.

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

    def evaluate(self, X: np.ndarray, y=None) -> float:
        """
        Compute opposite of inertia (for scoring).

        Parameters
        ----------
        X : array-like of shape (n_samples, n_features)
            Samples.
        y : Ignored
            Not used.

        Returns
        -------
        score : float
            Opposite of inertia.
        """
        check_is_trained(self)
        X = check_array(X)

        _, inertia = self._assign_labels(X, self.cluster_centers_)
        return -inertia

    def __nalyst_tags__(self) -> LearnerTags:
        return LearnerTags(
            learner_type="clusterer",
            target_tags=TargetTags(required=False),
        )


class MiniBatchKMeans(ClusterMixin, TransformerMixin, BaseLearner):
    """
    Mini-Batch K-Means clustering.

    Uses mini-batches for faster training on large datasets.

    Parameters
    ----------
    n_clusters : int, default=8
        Number of clusters.
    init : {"k-means++", "random"} or ndarray, default="k-means++"
        Initialization method.
    max_iter : int, default=100
        Maximum number of iterations.
    batch_size : int, default=1024
        Size of mini-batches.
    verbose : int, default=0
        Verbosity level.
    random_state : int, optional
        Random seed.
    tol : float, default=0.0
        Convergence tolerance.
    max_no_improvement : int, default=10
        Early stopping.
    init_size : int, optional
        Number of samples for initialization.
    n_init : int, default=3
        Number of random initializations.
    reassignment_ratio : float, default=0.01
        Fraction of centers to reassign.

    Attributes
    ----------
    cluster_centers_ : ndarray of shape (n_clusters, n_features)
        Coordinates of cluster centers.
    labels_ : ndarray of shape (n_samples,)
        Labels of each point.
    inertia_ : float
        Sum of squared distances to closest centroid.
    n_iter_ : int
        Number of iterations.

    Examples
    --------
    >>> import numpy as np
    >>> from nalyst.clustering import MiniBatchKMeans
    >>> X = np.random.randn(1000, 5)
    >>> kmeans = MiniBatchKMeans(n_clusters=3, batch_size=100, random_state=42)
    >>> kmeans.train(X)
    MiniBatchKMeans(batch_size=100, n_clusters=3, random_state=42)
    """

    def __init__(
        self,
        n_clusters: int = 8,
        *,
        init: Union[str, np.ndarray] = "k-means++",
        max_iter: int = 100,
        batch_size: int = 1024,
        verbose: int = 0,
        random_state: Optional[int] = None,
        tol: float = 0.0,
        max_no_improvement: int = 10,
        init_size: Optional[int] = None,
        n_init: int = 3,
        reassignment_ratio: float = 0.01,
    ):
        self.n_clusters = n_clusters
        self.init = init
        self.max_iter = max_iter
        self.batch_size = batch_size
        self.verbose = verbose
        self.random_state = random_state
        self.tol = tol
        self.max_no_improvement = max_no_improvement
        self.init_size = init_size
        self.n_init = n_init
        self.reassignment_ratio = reassignment_ratio

    def _init_centroids(
        self,
        X: np.ndarray,
        rng: np.random.RandomState,
    ) -> np.ndarray:
        """Initialize centroids."""
        if isinstance(self.init, np.ndarray):
            return self.init.copy()
        elif self.init == "k-means++":
            return _kmeans_plusplus_init(X, self.n_clusters, rng)
        else:  # random
            indices = rng.choice(len(X), self.n_clusters, replace=False)
            return X[indices].copy()

    def train(self, X: np.ndarray, y=None) -> "MiniBatchKMeans":
        """
        Compute mini-batch k-means clustering.

        Parameters
        ----------
        X : array-like of shape (n_samples, n_features)
            Training data.
        y : Ignored
            Not used.

        Returns
        -------
        self : MiniBatchKMeans
        """
        X = check_array(X)
        n_samples, n_features = X.shape
        self.n_features_in_ = n_features

        rng = check_random_state(self.random_state)

        # Initialize from subset if needed
        if self.init_size is not None and self.init_size < n_samples:
            init_indices = rng.choice(n_samples, self.init_size, replace=False)
            X_init = X[init_indices]
        else:
            X_init = X

        # Best initialization
        best_inertia = None
        best_centers = None

        for init_run in range(self.n_init):
            centers = self._init_centroids(X_init, rng)

            # Per-center sample counts for running average
            counts = np.zeros(self.n_clusters)
            no_improvement = 0
            prev_inertia = None

            for iteration in range(self.max_iter):
                # Sample mini-batch
                batch_indices = rng.choice(
                    n_samples,
                    min(self.batch_size, n_samples),
                    replace=False
                )
                X_batch = X[batch_indices]

                # Assign to nearest center
                distances = _euclidean_distances(X_batch, centers)
                labels = np.argmin(distances, axis=1)

                # Update centers with streaming average
                for k in range(self.n_clusters):
                    mask = labels == k
                    if np.any(mask):
                        n_new = np.sum(mask)
                        counts[k] += n_new
                        eta = n_new / counts[k]
                        centers[k] = (1 - eta) * centers[k] + eta * X_batch[mask].mean(axis=0)

                # Compute inertia on batch
                batch_inertia = np.sum(np.min(distances, axis=1) ** 2)

                if self.verbose and iteration % 10 == 0:
                    print(f"Iteration {iteration}, batch inertia: {batch_inertia:.4f}")

                # Early stopping
                if self.tol > 0:
                    if prev_inertia is not None:
                        if prev_inertia - batch_inertia < self.tol:
                            no_improvement += 1
                        else:
                            no_improvement = 0
                    prev_inertia = batch_inertia

                    if no_improvement >= self.max_no_improvement:
                        break

            # Compute final inertia
            distances = _euclidean_distances(X, centers)
            labels = np.argmin(distances, axis=1)
            inertia = np.sum(np.min(distances, axis=1) ** 2)

            if best_inertia is None or inertia < best_inertia:
                best_inertia = inertia
                best_centers = centers

        self.cluster_centers_ = best_centers

        # Final assignment
        distances = _euclidean_distances(X, self.cluster_centers_)
        self.labels_ = np.argmin(distances, axis=1)
        self.inertia_ = np.sum(np.min(distances, axis=1) ** 2)
        self.n_iter_ = iteration + 1

        return self

    def infer(self, X: np.ndarray) -> np.ndarray:
        """Predict cluster labels."""
        check_is_trained(self)
        X = check_array(X)

        distances = _euclidean_distances(X, self.cluster_centers_)
        return np.argmin(distances, axis=1)

    def transform(self, X: np.ndarray) -> np.ndarray:
        """Transform to cluster-distance space."""
        check_is_trained(self)
        X = check_array(X)

        return _euclidean_distances(X, self.cluster_centers_)

    def __nalyst_tags__(self) -> LearnerTags:
        return LearnerTags(
            learner_type="clusterer",
            target_tags=TargetTags(required=False),
        )
